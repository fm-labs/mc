import {readCached} from "@/utils/session-cache.ts";

// Subset of the Docker Engine API `GET /info` response (docker SDK `client.info()`)
export type DockerInfo = {
    Name?: string
    ServerVersion?: string
    OperatingSystem?: string
    OSType?: string
    Architecture?: string
    KernelVersion?: string
    NCPU?: number
    MemTotal?: number
    Driver?: string
    DockerRootDir?: string
    Containers?: number
    ContainersRunning?: number
    ContainersPaused?: number
    ContainersStopped?: number
    Images?: number
    Swarm?: { LocalNodeState?: string }
    Warnings?: string[] | null
}

// Subset of the Docker Engine API `GET /system/df` response (docker SDK `client.df()`)
export type DockerDf = {
    LayersSize?: number
    Images?: {
        Id: string
        RepoTags?: string[] | null
        Size?: number
        SharedSize?: number
        Containers?: number
    }[] | null
    Containers?: {
        Id: string
        Names?: string[]
        Image?: string
        State?: string
        SizeRw?: number
        SizeRootFs?: number
    }[] | null
    Volumes?: {
        Name: string
        UsageData?: { Size?: number, RefCount?: number } | null
    }[] | null
    BuildCache?: {
        ID: string
        Size?: number
        InUse?: boolean
        Shared?: boolean
    }[] | null
}

export type DiskUsage = {
    images: number
    containers: number
    volumes: number
    buildCache: number
}

export type HostStats = {
    hostId: string
    info?: DockerInfo
    df?: DockerDf
    infoTimestamp?: number
    dfTimestamp?: number
    containers: { total: number, running: number, paused: number, stopped: number }
    imageCount: number
    volumeCount: number
    disk?: DiskUsage
    reclaimable?: DiskUsage
    topImages: { name: string, size: number }[]
}

// Docker reports -1 when a size was not computed
const size = (n?: number | null) => (typeof n === "number" && n > 0 ? n : 0);

const sum = <T, >(items: T[] | null | undefined, fn: (item: T) => number) =>
    (items ?? []).reduce((acc, item) => acc + fn(item), 0);

const imageName = (img: NonNullable<DockerDf["Images"]>[number]) => {
    const tag = img.RepoTags?.find((t) => t !== "<none>:<none>");
    return tag ?? img.Id.replace("sha256:", "").slice(0, 12);
};

const diskUsage = (df: DockerDf): DiskUsage => ({
    // same as `docker system df`: layers are counted once
    images: size(df.LayersSize) || sum(df.Images, (i) => size(i.Size) - size(i.SharedSize)),
    containers: sum(df.Containers, (c) => size(c.SizeRw)),
    volumes: sum(df.Volumes, (v) => size(v.UsageData?.Size)),
    buildCache: sum(df.BuildCache?.filter((b) => !b.Shared), (b) => size(b.Size)),
});

const reclaimableUsage = (df: DockerDf): DiskUsage => ({
    images: sum(df.Images?.filter((i) => !i.Containers), (i) => size(i.Size) - size(i.SharedSize)),
    containers: sum(df.Containers?.filter((c) => c.State !== "running"), (c) => size(c.SizeRw)),
    volumes: sum(df.Volumes?.filter((v) => !v.UsageData?.RefCount), (v) => size(v.UsageData?.Size)),
    buildCache: sum(df.BuildCache?.filter((b) => !b.InUse && !b.Shared), (b) => size(b.Size)),
});

const containerCounts = (info?: DockerInfo, df?: DockerDf) => {
    if (info && typeof info.Containers === "number") {
        return {
            total: info.Containers,
            running: info.ContainersRunning ?? 0,
            paused: info.ContainersPaused ?? 0,
            stopped: info.ContainersStopped ?? 0,
        };
    }
    const list = df?.Containers ?? [];
    const running = list.filter((c) => c.State === "running").length;
    const paused = list.filter((c) => c.State === "paused").length;
    return {total: list.length, running, paused, stopped: list.length - running - paused};
};

// Build stats for a host from the browser session cache only (never calls the API).
// Keys match the ones written by ContainerHostProvider.fetchContainerData.
export const readHostStats = (hostId: string): HostStats | null => {
    const info = readCached<DockerInfo>(`container_host_${hostId}_path_info`);
    const df = readCached<DockerDf>(`container_host_${hostId}_path_df`);
    if (!info?.data && !df?.data) {
        return null;
    }
    const dfData = df?.data;
    return {
        hostId,
        info: info?.data,
        df: dfData,
        infoTimestamp: info?.timestamp,
        dfTimestamp: df?.timestamp,
        containers: containerCounts(info?.data, dfData),
        imageCount: dfData?.Images?.length ?? info?.data?.Images ?? 0,
        volumeCount: dfData?.Volumes?.length ?? 0,
        disk: dfData ? diskUsage(dfData) : undefined,
        reclaimable: dfData ? reclaimableUsage(dfData) : undefined,
        topImages: (dfData?.Images ?? [])
            .map((i) => ({name: imageName(i), size: size(i.Size)}))
            .sort((a, b) => b.size - a.size)
            .slice(0, 5),
    };
};

export const diskTotal = (d?: DiskUsage) => d ? d.images + d.containers + d.volumes + d.buildCache : 0;

export const formatBytes = (bytes: number, decimals = 1) => {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : decimals)} ${units[i]}`;
};

export const formatAge = (timestamp?: number) => {
    if (!timestamp) return "—";
    const s = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
    if (s < 60) return `${s}s ago`;
    if (s < 3600) return `${Math.round(s / 60)}m ago`;
    if (s < 86400) return `${Math.round(s / 3600)}h ago`;
    return `${Math.round(s / 86400)}d ago`;
};
