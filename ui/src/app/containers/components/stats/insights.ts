// Pure functions that turn cached host stats into the insight tables and charts.
import {
    containerName,
    HostStats,
    imageName,
    isDangling,
    size,
} from "@/app/containers/components/stats/host-stats.ts";
import {DockerInfo} from "@/app/containers/components/stats/docker-types.ts";
import {DAY} from "@/app/containers/components/stats/format.ts";

export const LONG_STOPPED_DAYS = 30;
export const STALE_IMAGE_DAYS = 90;

const parseDate = (s?: string) => {
    // docker uses "0001-01-01T00:00:00Z" for "never"
    if (!s || s.startsWith("0001-")) return undefined;
    const t = Date.parse(s);
    return Number.isNaN(t) ? undefined : t;
};

const withContainers = (stats: HostStats[]) =>
    stats.flatMap((s) => (s.containerList ?? []).map((c) => ({hostId: s.hostId, c})));

export const hostsWithContainerList = (stats: HostStats[]) => stats.filter((s) => s.containerList).length;

// --- Needs attention ---------------------------------------------------------------------------

export type AttentionKind = "unhealthy" | "restarting" | "oom" | "exited" | "long-stopped";

export type AttentionItem = {
    hostId: string
    containerId: string
    name: string
    image?: string
    kind: AttentionKind
    detail: string
}

export const attentionItems = (stats: HostStats[]): AttentionItem[] => {
    const now = Date.now();
    const items: AttentionItem[] = [];
    withContainers(stats).forEach(({hostId, c}) => {
        const base = {hostId, containerId: c.Id, name: containerName(c), image: c.Config?.Image};
        const st = c.State ?? {};
        if (st.Health?.Status === "unhealthy") {
            items.push({...base, kind: "unhealthy", detail: `health check failing ${st.Health.FailingStreak ?? "?"}x`});
        }
        if (st.Restarting || (c.RestartCount ?? 0) > 0) {
            items.push({...base, kind: "restarting", detail: `${c.RestartCount ?? 0} restarts${st.Restarting ? ", restarting now" : ""}`});
        }
        if (st.OOMKilled) {
            items.push({...base, kind: "oom", detail: "killed: out of memory"});
        }
        if (st.Status === "exited" || st.Status === "dead") {
            const finished = parseDate(st.FinishedAt);
            if (st.ExitCode) {
                items.push({...base, kind: "exited", detail: `exit code ${st.ExitCode}`});
            } else if (finished && now - finished > LONG_STOPPED_DAYS * DAY) {
                items.push({...base, kind: "long-stopped", detail: `stopped ${Math.round((now - finished) / DAY)} days`});
            }
        }
    });
    const order: AttentionKind[] = ["unhealthy", "oom", "restarting", "exited", "long-stopped"];
    return items.sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind));
};

// --- Resource limits and restart policy --------------------------------------------------------

export type PolicyRow = {
    hostId: string
    containerId: string
    name: string
    running: boolean
    noLimits: boolean
    noRestart: boolean
}

export const policyRows = (stats: HostStats[]): PolicyRow[] =>
    withContainers(stats)
        .map(({hostId, c}) => {
            const hc = c.HostConfig ?? {};
            return {
                hostId,
                containerId: c.Id,
                name: containerName(c),
                running: c.State?.Status === "running",
                noLimits: !hc.Memory && !hc.NanoCpus && !hc.CpuQuota,
                noRestart: !hc.RestartPolicy?.Name || hc.RestartPolicy.Name === "no",
            };
        })
        .filter((r) => r.noLimits || r.noRestart)
        .sort((a, b) => Number(b.running) - Number(a.running));

// --- Images ------------------------------------------------------------------------------------

export type ImageRow = {
    hostId: string
    id: string
    name: string
    size: number
    created?: number
    containers: number
    running: number
    dangling: boolean
}

export const imageRows = (stats: HostStats[]): ImageRow[] =>
    stats.flatMap((s) => {
        const runningByImage = new Map<string, number>();
        const allByImage = new Map<string, number>();
        s.containerList?.forEach((c) => {
            if (!c.Image) return;
            allByImage.set(c.Image, (allByImage.get(c.Image) ?? 0) + 1);
            if (c.State?.Status === "running") runningByImage.set(c.Image, (runningByImage.get(c.Image) ?? 0) + 1);
        });
        const createdById = new Map(s.imageList?.map((i) => [i.Id, parseDate(i.Created)]) ?? []);
        const images = s.df?.Images ?? s.imageList?.map((i) => ({...i, Created: undefined, Containers: undefined})) ?? [];
        return images.map((i) => ({
            hostId: s.hostId,
            id: i.Id,
            name: imageName(i),
            size: size(i.Size),
            created: i.Created ? i.Created * 1000 : createdById.get(i.Id),
            containers: size(i.Containers) || allByImage.get(i.Id) || 0,
            running: runningByImage.get(i.Id) ?? 0,
            dangling: isDangling(i),
        }));
    });

export const staleImages = (rows: ImageRow[]) => {
    const now = Date.now();
    return rows
        .filter((r) => r.running > 0 && r.created && now - r.created > STALE_IMAGE_DAYS * DAY)
        .sort((a, b) => (a.created ?? 0) - (b.created ?? 0));
};

// image age buckets for running containers' images
export const imageAgeBuckets = (rows: ImageRow[]) => {
    const now = Date.now();
    const buckets = [
        {bucket: "< 7d", max: 7},
        {bucket: "7-30d", max: 30},
        {bucket: "30-90d", max: 90},
        {bucket: "90-365d", max: 365},
        {bucket: "> 1y", max: Infinity},
    ].map((b) => ({...b, inUse: 0, unused: 0}));
    rows.forEach((r) => {
        if (!r.created) return;
        const days = (now - r.created) / DAY;
        const b = buckets.find((b) => days < b.max)!;
        if (r.containers > 0) b.inUse += 1; else b.unused += 1;
    });
    return buckets.map(({bucket, inUse, unused}) => ({bucket, inUse, unused}));
};

// --- Volumes -----------------------------------------------------------------------------------

export type VolumeRow = {
    hostId: string
    name: string
    size: number
    refCount: number
    usedBy: string[]
}

export const volumeRows = (stats: HostStats[]): VolumeRow[] =>
    stats.flatMap((s) => {
        const users = new Map<string, string[]>();
        s.containerList?.forEach((c) => c.Mounts?.forEach((m) => {
            if (m.Type === "volume" && m.Name) {
                users.set(m.Name, [...(users.get(m.Name) ?? []), containerName(c)]);
            }
        }));
        return (s.df?.Volumes ?? []).map((v) => ({
            hostId: s.hostId,
            name: v.Name,
            size: size(v.UsageData?.Size),
            refCount: size(v.UsageData?.RefCount),
            usedBy: users.get(v.Name) ?? [],
        }));
    }).sort((a, b) => b.size - a.size);

// --- Ports -------------------------------------------------------------------------------------

export type PortRow = {
    hostId: string
    hostPort: string
    hostIp: string
    containerPort: string
    container: string
    running: boolean
    public: boolean
    conflict: boolean
}

const PUBLIC_IPS = ["", "0.0.0.0", "::"];

export const portRows = (stats: HostStats[]): PortRow[] => {
    const rows: PortRow[] = [];
    withContainers(stats).forEach(({hostId, c}) => {
        // configured bindings, so stopped containers show up too
        const bindings = c.HostConfig?.PortBindings ?? {};
        const seen = new Set<string>();
        Object.entries(bindings).forEach(([containerPort, list]) => (list ?? []).forEach((b) => {
            const hostIp = b.HostIp ?? "";
            const hostPort = b.HostPort || "random";
            const k = `${containerPort}|${hostPort}|${PUBLIC_IPS.includes(hostIp) ? "*" : hostIp}`;
            if (seen.has(k)) return; // 0.0.0.0 and :: of the same binding
            seen.add(k);
            rows.push({
                hostId, hostPort, hostIp: hostIp || "0.0.0.0", containerPort,
                container: containerName(c),
                running: c.State?.Status === "running",
                public: PUBLIC_IPS.includes(hostIp),
                conflict: false,
            });
        }));
    });
    // the same fixed host port bound by more than one container on a host
    const counts = new Map<string, Set<string>>();
    rows.forEach((r) => {
        if (r.hostPort === "random") return;
        const k = `${r.hostId}|${r.hostPort}|${r.containerPort.split("/")[1] ?? "tcp"}`;
        counts.set(k, (counts.get(k) ?? new Set()).add(r.container));
    });
    rows.forEach((r) => {
        const k = `${r.hostId}|${r.hostPort}|${r.containerPort.split("/")[1] ?? "tcp"}`;
        r.conflict = (counts.get(k)?.size ?? 0) > 1;
    });
    return rows.sort((a, b) =>
        Number(b.conflict) - Number(a.conflict)
        || a.hostId.localeCompare(b.hostId)
        || (parseInt(a.hostPort) || 0) - (parseInt(b.hostPort) || 0));
};

// --- Compose projects --------------------------------------------------------------------------

export type ComposeProject = {
    hostId: string
    project: string
    workingDir?: string
    services: string[]
    running: number
    total: number
}

export const composeProjects = (stats: HostStats[]): ComposeProject[] => {
    const map = new Map<string, ComposeProject>();
    withContainers(stats).forEach(({hostId, c}) => {
        const labels = c.Config?.Labels ?? {};
        const project = labels["com.docker.compose.project"];
        if (!project) return;
        const k = `${hostId}|${project}`;
        const p = map.get(k) ?? {hostId, project, workingDir: labels["com.docker.compose.project.working_dir"], services: [], running: 0, total: 0};
        const service = labels["com.docker.compose.service"];
        if (service && !p.services.includes(service)) p.services.push(service);
        p.total += 1;
        if (c.State?.Status === "running") p.running += 1;
        map.set(k, p);
    });
    return [...map.values()].sort((a, b) =>
        (a.running === a.total ? 1 : 0) - (b.running === b.total ? 1 : 0)
        || a.project.localeCompare(b.project));
};

export const unmanagedContainerCount = (stats: HostStats[]) =>
    withContainers(stats).filter(({c}) => !c.Config?.Labels?.["com.docker.compose.project"]).length;

// --- Hosts: version drift and density ----------------------------------------------------------

export const driftFields: { key: keyof DockerInfo, label: string }[] = [
    {key: "ServerVersion", label: "Docker"},
    {key: "OperatingSystem", label: "OS"},
    {key: "KernelVersion", label: "Kernel"},
    {key: "Architecture", label: "Arch"},
    {key: "Driver", label: "Storage"},
    {key: "CgroupVersion", label: "cgroup"},
];

// most common value per field; other values count as drift
export const majorityValues = (stats: HostStats[]) => {
    const result: Partial<Record<keyof DockerInfo, string>> = {};
    driftFields.forEach(({key}) => {
        const counts = new Map<string, number>();
        stats.forEach((s) => {
            const v = s.info?.[key];
            if (v !== undefined && v !== "") counts.set(String(v), (counts.get(String(v)) ?? 0) + 1);
        });
        const top = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
        if (top && counts.size > 1) result[key] = top[0];
    });
    return result;
};

export const densityRows = (stats: HostStats[]) =>
    stats
        .filter((s) => s.info?.NCPU && s.info?.MemTotal)
        .map((s) => ({
            host: s.hostId,
            perCpu: +(s.containers.running / s.info!.NCPU!).toFixed(2),
            perGb: +(s.containers.running / (s.info!.MemTotal! / 1024 ** 3)).toFixed(2),
            running: s.containers.running,
            cpus: s.info!.NCPU!,
            memory: s.info!.MemTotal!,
        }));

export const warningRows = (stats: HostStats[]) =>
    stats.flatMap((s) => (s.info?.Warnings ?? []).map((w) => ({hostId: s.hostId, warning: w})));
