import {
    ContainerNode,
    Graph,
    GraphNode,
    NetworkNode,
    networkNodeWidth,
    PublishedPort,
} from "@/app/containers/components/network/network-graph.ts";
import {
    EdgeRole,
    Extent,
    hostBox,
    hostIdsOf,
    Layout,
    nodeExtent,
    packHosts,
    Point,
} from "@/app/containers/components/network/network-layout.ts";

// Org-chart geometry: host on top, networks in a row, containers stacked below their network
export const TREE = {
    networkY: 150,
    firstRowGap: 78,
    rowGap: 12,
    childIndent: 40,
    columnMin: 260,
    columnGap: 28,
    // containers sit this far right of the column's left edge; the connector spine runs left of them
    containerInset: 44,
    spineInset: 18,
};

// ---- container cards: name, IP addresses and published ports next to the container icon ----

// Card geometry, relative to the container's center (the icon sits in the card's top-left corner)
export const CARD = {
    left: -24,
    top: -24,
    width: 236,
    textX: 26,
    nameH: 10, // name baseline is at y = -4, the next line starts at 6
    ipH: 14,
    portRowH: 19,
    portPillH: 15,
    portGap: 4,
    padBottom: 8,
    minHeight: 48,
};

export type ContainerCard = {
    ips: { ip: string, network: string }[]
    portRows: string[][]
    height: number
}

const WILDCARD_IPS = ["", "0.0.0.0", "::"];

export const portLabel = (p: PublishedPort) =>
    `${p.ip && !WILDCARD_IPS.includes(p.ip) ? `${p.ip}:` : ""}${p.publicPort}→${p.privatePort}${p.type && p.type !== "tcp" ? `/${p.type}` : ""}`;

export const portPillWidth = (label: string) => label.length * 6.1 + 12;

const cardCache = new WeakMap<ContainerNode, ContainerCard>();

export const containerCard = (c: ContainerNode): ContainerCard => {
    const hit = cardCache.get(c);
    if (hit) return hit;
    const ips = c.attachments.flatMap((a) =>
        [a.ipv4, a.ipv6].filter((ip): ip is string => !!ip).map((ip) => ({ip, network: a.networkName})));
    // IPv4 and IPv6 bindings of the same port show up twice
    const labels = [...new Set(c.ports.filter((p) => p.publicPort).map(portLabel))];
    const maxRow = CARD.left + CARD.width - CARD.textX - 8;
    const portRows: string[][] = [];
    let row: string[] = [], rowW = 0;
    labels.forEach((l) => {
        const w = portPillWidth(l);
        if (row.length && rowW + w > maxRow) {
            portRows.push(row);
            row = [];
            rowW = 0;
        }
        row.push(l);
        rowW += w + CARD.portGap;
    });
    if (row.length) portRows.push(row);
    const content = 6 + ips.length * CARD.ipH + portRows.length * CARD.portRowH;
    const height = ips.length || portRows.length
        ? Math.max(CARD.minHeight, content - CARD.top + CARD.padBottom)
        : CARD.minHeight;
    const card = {ips, portRows, height};
    cardCache.set(c, card);
    return card;
};

// Tree containers are drawn as cards
export const treeExtent = (n: GraphNode): Extent =>
    n.kind === "container"
        ? {x: -CARD.left, right: CARD.left + CARD.width, top: -CARD.top, bottom: CARD.top + containerCard(n).height}
        : nodeExtent(n);

const byName = (a: { label: string }, b: { label: string }) => a.label.localeCompare(b.label);

const layoutHostTree = (graph: Graph, hostId: string, roles: Record<string, EdgeRole>): Record<string, Point> => {
    const nodes = graph.nodes.filter((n) => n.hostId === hostId);
    const edges = graph.edges.filter((e) => e.hostId === hostId);
    const host = nodes.find((n) => n.kind === "host")!;
    const networks = nodes.filter((n): n is NetworkNode => n.kind === "network");
    const containers = nodes.filter((n): n is ContainerNode => n.kind === "container");

    const netEdges = edges.filter((e) => e.kind === "network-container");
    const memberCount = new Map<string, number>();
    netEdges.forEach((e) => memberCount.set(e.source, (memberCount.get(e.source) ?? 0) + 1));
    const netById = new Map(networks.map((n) => [n.id, n]));

    // Each container hangs below one network: a custom one first, then the busiest
    const rank = (n: NetworkNode) => [n.builtin ? 1 : 0, -(memberCount.get(n.id) ?? 0)];
    const compare = (a: NetworkNode, b: NetworkNode) => {
        const [ra, rb] = [rank(a), rank(b)];
        return ra[0] - rb[0] || ra[1] - rb[1] || byName(a, b);
    };
    const primary = new Map<string, string>(); // container id -> network id
    containers.forEach((c) => {
        const options = netEdges.filter((e) => e.target === c.id).map((e) => netById.get(e.source)).filter((n): n is NetworkNode => !!n);
        options.sort(compare);
        if (options[0]) primary.set(c.id, options[0].id);
    });
    netEdges.forEach((e) => { roles[e.id] = primary.get(e.target) === e.source ? "tree" : "cross"; });
    edges.filter((e) => e.kind === "host-network").forEach((e) => { roles[e.id] = "tree"; });

    // Containers sharing another container's network stack hang below that container
    const parentOf = new Map<string, string>();
    edges.filter((e) => e.kind === "container-container").forEach((e) => {
        const tree = !primary.has(e.source);
        roles[e.id] = tree ? "tree" : "cross";
        if (tree) parentOf.set(e.source, e.target);
    });
    const childrenOf = new Map<string, ContainerNode[]>();
    containers.forEach((c) => {
        const p = parentOf.get(c.id);
        if (p) (childrenOf.get(p) ?? childrenOf.set(p, []).get(p)!).push(c);
    });

    // Columns: one per network, plus one for containers without a visible network
    const sortContainers = (list: ContainerNode[]) =>
        list.sort((a, b) => (a.project ?? "~").localeCompare(b.project ?? "~") || byName(a, b));
    const columns: { network?: NetworkNode, members: ContainerNode[] }[] = [...networks].sort(compare).map((n) => ({
        network: n,
        members: sortContainers(containers.filter((c) => primary.get(c.id) === n.id && !parentOf.has(c.id))),
    }));
    const detached = sortContainers(containers.filter((c) => !primary.has(c.id) && !parentOf.has(c.id)));
    if (detached.length) columns.push({members: detached});

    // nesting depth of shared-stack containers, so wide columns get enough room
    const depthOf = (c: ContainerNode) => {
        let d = 0, id: string | undefined = c.id;
        const seen = new Set<string>();
        while ((id = parentOf.get(id)) && !seen.has(id)) { seen.add(id); d++; }
        return d;
    };
    // top-most container of a shared-stack chain
    const rootOf = (c: ContainerNode) => {
        let id = c.id;
        const seen = new Set<string>();
        while (parentOf.has(id) && !seen.has(id)) { seen.add(id); id = parentOf.get(id)!; }
        return id;
    };
    // column members are roots, so their descendants' depth is relative to the column
    const maxDepth = (members: ContainerNode[]) => {
        const ids = new Set(members.map((m) => m.id));
        return Math.max(0, ...containers.filter((c) => ids.has(rootOf(c))).map(depthOf));
    };
    const rowStep = (c: ContainerNode) => containerCard(c).height + TREE.rowGap;

    const positions: Record<string, Point> = {[host.id]: {x: 0, y: 0}};
    const widths = columns.map((col) => Math.max(
        TREE.columnMin,
        TREE.containerInset + maxDepth(col.members) * TREE.childIndent + CARD.left + CARD.width + 8,
        col.network ? networkNodeWidth(col.network) + 16 : 0));
    const total = widths.reduce((a, b) => a + b, 0) + TREE.columnGap * Math.max(0, columns.length - 1);
    let left = -total / 2;

    columns.forEach((col, i) => {
        const w = widths[i];
        if (col.network) positions[col.network.id] = {x: left + w / 2, y: TREE.networkY};
        let y = TREE.networkY + TREE.firstRowGap;
        const place = (c: ContainerNode, depth: number, seen: Set<string>) => {
            if (seen.has(c.id)) return;
            seen.add(c.id);
            positions[c.id] = {x: left + TREE.containerInset + depth * TREE.childIndent, y};
            y += rowStep(c);
            sortContainers(childrenOf.get(c.id) ?? []).forEach((child) => place(child, depth + 1, seen));
        };
        const seen = new Set<string>();
        col.members.forEach((c) => place(c, 0, seen));
        left += w + TREE.columnGap;
    });

    // anything left over (e.g. a shared-stack cycle) goes below the host
    let extraY = TREE.networkY + TREE.firstRowGap;
    containers.filter((c) => !positions[c.id]).forEach((c) => {
        positions[c.id] = {x: left + TREE.containerInset, y: extraY};
        extraY += rowStep(c);
    });
    return positions;
};

export const layoutTree = (graph: Graph): Layout => {
    const edgeRoles: Record<string, EdgeRole> = {};
    const parts = hostIdsOf(graph).map((hostId) => {
        const positions = layoutHostTree(graph, hostId, edgeRoles);
        const nodes = graph.nodes.filter((n) => n.hostId === hostId);
        return {positions, box: hostBox(hostId, nodes, positions, treeExtent)!};
    });
    return {mode: "tree", edgeRoles, ...packHosts(parts)};
};
