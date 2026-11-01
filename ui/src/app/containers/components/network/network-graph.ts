import {readCached} from "@/utils/session-cache.ts";
import {DockerDf, DockerInfo} from "@/app/containers/components/stats/docker-types.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

// same as BUILTIN_NETWORKS in docker-network-details-dialog (kept here so this module has no UI imports)
const BUILTIN_NETWORKS = ["bridge", "host", "none"];

// Paths the network view reads from the session cache (same keys as ContainerHostProvider.fetchContainerData)
export const NETWORK_PATHS = ["networks", "df"];

export const hostCacheKey = (hostId: string, path: string) => `container_host_${hostId}_path_${path}`;

export type HostNetworkData = {
    hostId: string
    info?: DockerInfo
    networks?: any[]
    df?: DockerDf & { Containers?: any[] | null }
    containers?: any[]
    cachedAt?: number
}

// Read everything the diagram needs for one host from the session cache (never calls the API)
export const readHostNetworkData = (hostId: string): HostNetworkData | null => {
    const networks = readCached<any[]>(hostCacheKey(hostId, "networks"));
    const df = readCached<any>(hostCacheKey(hostId, "df"));
    const containers = readCached<any[]>(hostCacheKey(hostId, "containers"));
    const info = readCached<DockerInfo>(hostCacheKey(hostId, "info"));
    if (!Array.isArray(networks?.data) && !df?.data && !Array.isArray(containers?.data)) {
        return null;
    }
    const times = [networks?.timestamp, df?.timestamp, containers?.timestamp].filter((t): t is number => !!t);
    return {
        hostId,
        info: info?.data ?? undefined,
        networks: Array.isArray(networks?.data) ? networks.data : undefined,
        df: df?.data ?? undefined,
        containers: Array.isArray(containers?.data) ? containers.data : undefined,
        cachedAt: times.length ? Math.min(...times) : undefined,
    };
};

export type Attachment = {
    networkName: string
    networkId?: string
    ipv4?: string
    ipv6?: string
    mac?: string
    gateway?: string
    aliases?: string[]
}

export type PublishedPort = { ip?: string, publicPort?: number, privatePort: number, type?: string }

export type HostNode = {
    kind: "host"
    id: string
    hostId: string
    label: string
    info?: DockerInfo
}

export type NetworkNode = {
    kind: "network"
    id: string
    hostId: string
    label: string
    networkId?: string
    driver?: string
    scope?: string
    subnets: string[]
    gateways: string[]
    internal?: boolean
    attachable?: boolean
    ipv6?: boolean
    builtin: boolean
    project?: string
    // only known from container data, not from the network list
    synthetic: boolean
}

export type ContainerNode = {
    kind: "container"
    id: string
    hostId: string
    label: string
    containerId: string
    state?: string
    status?: string
    health?: string
    image?: string
    project?: string
    service?: string
    networkMode?: string
    attachments: Attachment[]
    ports: PublishedPort[]
}

export type GraphNode = HostNode | NetworkNode | ContainerNode

export type EdgeKind = "host-network" | "network-container" | "container-container"

export type GraphEdge = {
    id: string
    kind: EdgeKind
    source: string
    target: string
    hostId: string
    ip?: string
}

export type Graph = { nodes: GraphNode[], edges: GraphEdge[] }

export type GraphFilter = {
    showBuiltin: boolean
    showUnused: boolean
    showStopped: boolean
}

const ACTIVE_STATES = ["running", "paused", "restarting"];
export const isActive = (c: ContainerNode) => ACTIVE_STATES.includes(c.state ?? "");

const nonEmpty = (s?: string | null) => (s ? s : undefined);

const attachmentsOf = (networks: Record<string, any> | undefined | null): Attachment[] =>
    Object.entries(networks ?? {}).map(([name, s]) => ({
        networkName: name,
        networkId: nonEmpty(s?.NetworkID),
        ipv4: nonEmpty(s?.IPAddress),
        ipv6: nonEmpty(s?.GlobalIPv6Address),
        mac: nonEmpty(s?.MacAddress),
        gateway: nonEmpty(s?.Gateway),
        aliases: Array.isArray(s?.Aliases) ? s.Aliases : undefined,
    }));

// `docker system df` / list format: [{PrivatePort, PublicPort, Type, IP}]
const portsFromSummary = (ports?: any[] | null): PublishedPort[] =>
    (ports ?? []).map((p) => ({ip: p.IP, publicPort: p.PublicPort, privatePort: p.PrivatePort, type: p.Type}));

// `docker inspect` format: {"80/tcp": [{HostIp, HostPort}]}
const portsFromInspect = (ports?: Record<string, any[] | null> | null): PublishedPort[] =>
    Object.entries(ports ?? {}).flatMap(([key, bindings]) => {
        const [port, type] = key.split("/");
        if (!bindings?.length) return [{privatePort: Number(port), type}];
        return bindings.map((b) => ({ip: b.HostIp, publicPort: Number(b.HostPort) || undefined, privatePort: Number(port), type}));
    });

const healthFromStatus = (status?: string) => {
    const m = status?.match(/\((healthy|unhealthy|health: starting)\)/);
    return m ? m[1].replace("health: ", "") : undefined;
};

// Merge the container list from `df` with the inspected containers (fuller and usually fresher)
const collectContainers = (hostId: string, data: HostNetworkData): Map<string, ContainerNode> => {
    const map = new Map<string, ContainerNode>();
    (data.df?.Containers ?? []).forEach((c: any) => {
        if (!c?.Id) return;
        map.set(c.Id, {
            kind: "container",
            id: `c:${hostId}:${c.Id}`,
            hostId,
            containerId: c.Id,
            label: (c.Names?.[0] ?? shortId(c.Id)).replace(/^\//, ""),
            state: c.State,
            status: c.Status,
            health: healthFromStatus(c.Status),
            image: c.Image,
            project: c.Labels?.["com.docker.compose.project"],
            service: c.Labels?.["com.docker.compose.service"],
            networkMode: c.HostConfig?.NetworkMode,
            attachments: attachmentsOf(c.NetworkSettings?.Networks),
            ports: portsFromSummary(c.Ports),
        });
    });
    (data.containers ?? []).forEach((c: any) => {
        if (!c?.Id) return;
        const prev = map.get(c.Id);
        const attachments = attachmentsOf(c.NetworkSettings?.Networks);
        const ports = portsFromInspect(c.NetworkSettings?.Ports);
        map.set(c.Id, {
            kind: "container",
            id: `c:${hostId}:${c.Id}`,
            hostId,
            containerId: c.Id,
            label: (c.Name ?? "").replace(/^\//, "") || prev?.label || shortId(c.Id),
            state: c.State?.Status ?? prev?.state,
            status: prev?.status,
            health: c.State?.Health?.Status ?? prev?.health,
            image: c.Config?.Image ?? prev?.image,
            project: c.Config?.Labels?.["com.docker.compose.project"] ?? prev?.project,
            service: c.Config?.Labels?.["com.docker.compose.service"] ?? prev?.service,
            networkMode: c.HostConfig?.NetworkMode ?? prev?.networkMode,
            attachments: attachments.length ? attachments : prev?.attachments ?? [],
            ports: ports.length ? ports : prev?.ports ?? [],
        });
    });
    return map;
};

// Estimated pill width of a network node, used by both the layout and the renderer
export const networkNodeWidth = (n: NetworkNode) =>
    Math.max(110, Math.min(220, 44 + Math.max(n.label.length, (n.subnets[0] ?? "").length * 0.85) * 7));

const buildHostGraph = (data: HostNetworkData, filter: GraphFilter): Graph => {
    const hostId = data.hostId;
    const hostNode: HostNode = {kind: "host", id: `h:${hostId}`, hostId, label: hostId, info: data.info};

    const networks = new Map<string, NetworkNode>(); // node id -> node
    const byNetId = new Map<string, NetworkNode>();
    const byNetName = new Map<string, NetworkNode>();

    (data.networks ?? []).forEach((n: any) => {
        if (!n?.Id) return;
        const ipam: any[] = n.IPAM?.Config ?? [];
        const node: NetworkNode = {
            kind: "network",
            id: `n:${hostId}:${n.Id}`,
            hostId,
            label: n.Name ?? shortId(n.Id),
            networkId: n.Id,
            driver: n.Driver,
            scope: n.Scope,
            subnets: ipam.map((c) => c?.Subnet).filter(Boolean),
            gateways: ipam.map((c) => c?.Gateway).filter(Boolean),
            internal: !!n.Internal,
            attachable: !!n.Attachable,
            ipv6: !!n.EnableIPv6,
            builtin: BUILTIN_NETWORKS.includes(n.Name),
            project: n.Labels?.["com.docker.compose.project"],
            synthetic: false,
        };
        networks.set(node.id, node);
        byNetId.set(n.Id, node);
        if (n.Name) byNetName.set(n.Name, node);
    });

    const resolveNetwork = (a: Attachment): NetworkNode => {
        const found = (a.networkId && byNetId.get(a.networkId)) || byNetName.get(a.networkName);
        if (found) return found;
        // network list not cached: derive the network from the container's settings
        const node: NetworkNode = {
            kind: "network",
            id: `n:${hostId}:${a.networkId ?? a.networkName}`,
            hostId,
            label: a.networkName,
            networkId: a.networkId,
            driver: a.networkName === "host" ? "host" : a.networkName === "none" ? "null" : undefined,
            subnets: [],
            gateways: a.gateway ? [a.gateway] : [],
            builtin: BUILTIN_NETWORKS.includes(a.networkName),
            synthetic: true,
        };
        networks.set(node.id, node);
        if (a.networkId) byNetId.set(a.networkId, node);
        byNetName.set(a.networkName, node);
        return node;
    };

    const containerMap = collectContainers(hostId, data);
    // The network list may carry its own Containers field (inspect format)
    (data.networks ?? []).forEach((n: any) => {
        Object.entries(n?.Containers ?? {}).forEach(([cid, c]: [string, any]) => {
            const existing = containerMap.get(cid);
            const attachment: Attachment = {
                networkName: n.Name,
                networkId: n.Id,
                ipv4: c?.IPv4Address?.replace(/\/\d+$/, "") || undefined,
                ipv6: c?.IPv6Address?.replace(/\/\d+$/, "") || undefined,
                mac: c?.MacAddress || undefined,
            };
            if (existing) {
                if (!existing.attachments.some((a) => a.networkId === n.Id || a.networkName === n.Name)) {
                    existing.attachments.push(attachment);
                }
            } else {
                containerMap.set(cid, {
                    kind: "container", id: `c:${hostId}:${cid}`, hostId, containerId: cid,
                    label: c?.Name ?? shortId(cid), attachments: [attachment], ports: [],
                });
            }
        });
    });

    let containers = [...containerMap.values()];
    if (!filter.showStopped) containers = containers.filter(isActive);

    const edges: GraphEdge[] = [];
    containers.forEach((c) => {
        c.attachments.forEach((a) => {
            const net = resolveNetwork(a);
            edges.push({
                id: `e:${net.id}>${c.id}`, kind: "network-container", hostId,
                source: net.id, target: c.id, ip: a.ipv4 ?? a.ipv6,
            });
        });
    });

    // network_mode: container:<name|id> shares the network stack of another container
    const byContainerRef = (ref: string) => containers.find((o) =>
        o.containerId === ref || o.containerId.startsWith(ref) || o.label === ref);
    containers.forEach((c) => {
        const ref = c.networkMode?.startsWith("container:") ? c.networkMode.slice("container:".length) : undefined;
        const target = ref ? byContainerRef(ref) : undefined;
        if (target && target.id !== c.id) {
            edges.push({id: `e:${c.id}>${target.id}`, kind: "container-container", hostId, source: c.id, target: target.id});
        }
    });

    let netList = [...networks.values()];
    if (!filter.showBuiltin) netList = netList.filter((n) => !n.builtin);
    if (!filter.showUnused) {
        const used = new Set(edges.map((e) => e.source));
        netList = netList.filter((n) => used.has(n.id));
    }
    const netIds = new Set(netList.map((n) => n.id));
    const kept = edges.filter((e) => e.kind !== "network-container" || netIds.has(e.source));

    netList.forEach((n) => kept.unshift({id: `e:${hostNode.id}>${n.id}`, kind: "host-network", hostId, source: hostNode.id, target: n.id}));

    return {nodes: [hostNode, ...netList, ...containers], edges: kept};
};

export const buildGraph = (hosts: HostNetworkData[], filter: GraphFilter): Graph => {
    const parts = hosts.map((h) => buildHostGraph(h, filter));
    return {nodes: parts.flatMap((p) => p.nodes), edges: parts.flatMap((p) => p.edges)};
};

// A stable string describing the graph's structure, so the layout only reruns when it changes
export const graphSignature = (g: Graph) =>
    g.nodes.map((n) => n.id).join("|") + "#" + g.edges.map((e) => e.id).join("|");

export type GraphSummary = {
    hosts: number
    networks: number
    customNetworks: number
    containers: number
    running: number
    multiHomed: number
    internal: number
}

export const summarize = (g: Graph): GraphSummary => {
    const nets = g.nodes.filter((n): n is NetworkNode => n.kind === "network");
    const containers = g.nodes.filter((n): n is ContainerNode => n.kind === "container");
    const netCount = new Map<string, number>();
    g.edges.filter((e) => e.kind === "network-container").forEach((e) => netCount.set(e.target, (netCount.get(e.target) ?? 0) + 1));
    return {
        hosts: g.nodes.filter((n) => n.kind === "host").length,
        networks: nets.length,
        customNetworks: nets.filter((n) => !n.builtin).length,
        containers: containers.length,
        running: containers.filter((c) => c.state === "running").length,
        multiHomed: containers.filter((c) => (netCount.get(c.id) ?? 0) > 1).length,
        internal: nets.filter((n) => n.internal).length,
    };
};
