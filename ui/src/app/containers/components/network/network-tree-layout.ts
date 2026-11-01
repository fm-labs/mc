import {ContainerNode, Graph, GraphNode, NetworkNode, networkNodeWidth} from "@/app/containers/components/network/network-graph.ts";
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
    rowStep: 56,
    childIndent: 32,
    columnMin: 210,
    columnGap: 28,
    // containers sit this far right of the column's left edge; the connector spine runs left of them
    containerInset: 44,
    spineInset: 18,
};

// Tree containers have their label on the right
export const treeExtent = (n: GraphNode): Extent =>
    n.kind === "container" ? {x: 24, right: 180, top: 22, bottom: 24} : nodeExtent(n);

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

    const positions: Record<string, Point> = {[host.id]: {x: 0, y: 0}};
    const widths = columns.map((col) => Math.max(TREE.columnMin, col.network ? networkNodeWidth(col.network) + 16 : 0));
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
            y += TREE.rowStep;
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
        extraY += TREE.rowStep;
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
