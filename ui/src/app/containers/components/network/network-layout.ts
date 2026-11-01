import {Graph, GraphEdge, GraphNode, networkNodeWidth} from "@/app/containers/components/network/network-graph.ts";

export type Point = { x: number, y: number }

export type HostBox = { hostId: string, x: number, y: number, w: number, h: number }

export type LayoutMode = "graph" | "tree"

// In the tree layout each edge is either part of the tree or an extra cross link
export type EdgeRole = "tree" | "cross"

export type Layout = {
    mode: LayoutMode
    positions: Record<string, Point>
    width: number
    height: number
    edgeRoles?: Record<string, EdgeRole>
}

export type Extent = { x: number, top: number, bottom: number, right?: number }

// Space a node needs around its center (labels included)
export const nodeRadius = (n: GraphNode) => {
    switch (n.kind) {
        case "host": return 48;
        case "network": return networkNodeWidth(n) / 2 + 8;
        default: return 34;
    }
};

// Extra room below a node for its label, used for the host boxes
export const nodeExtent = (n: GraphNode): Extent => {
    switch (n.kind) {
        case "host": return {x: 60, top: 36, bottom: 64};
        case "network": return {x: networkNodeWidth(n) / 2 + 6, top: 26, bottom: 26};
        default: return {x: 60, top: 22, bottom: 40};
    }
};

const CHARGE = {host: -1400, network: -800, container: -320};
const LINK_DISTANCE: Record<GraphEdge["kind"], number> = {
    "host-network": 170,
    "network-container": 110,
    "container-container": 70,
};
const TICKS = 320;

// Small deterministic PRNG so the same data always gives the same picture
const seeded = (seedText: string) => {
    let h = 2166136261;
    for (let i = 0; i < seedText.length; i++) h = Math.imul(h ^ seedText.charCodeAt(i), 16777619);
    let a = h >>> 0;
    return () => {
        a = (a + 0x6D2B79F5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
};

type SimNode = { node: GraphNode, x: number, y: number, vx: number, vy: number, r: number, fixed: boolean }

// Force-directed layout of one host, centered on the host node at (0, 0)
const layoutHost = (nodes: GraphNode[], edges: GraphEdge[]): Record<string, Point> => {
    const rand = seeded(nodes[0]?.id ?? "x");
    const sim: SimNode[] = nodes.map((node) => ({node, x: 0, y: 0, vx: 0, vy: 0, r: nodeRadius(node), fixed: node.kind === "host"}));
    const index = new Map(sim.map((s, i) => [s.node.id, i]));
    const links = edges
        .map((e) => ({s: index.get(e.source)!, t: index.get(e.target)!, d: LINK_DISTANCE[e.kind]}))
        .filter((l) => l.s !== undefined && l.t !== undefined);

    const degree = new Array(sim.length).fill(0);
    links.forEach((l) => { degree[l.s]++; degree[l.t]++; });

    // Seed: networks on a ring around the host, containers near the networks they join
    const nets = sim.filter((s) => s.node.kind === "network");
    const ring = Math.max(170, nets.length * 34);
    nets.forEach((s, i) => {
        const a = (i / Math.max(1, nets.length)) * Math.PI * 2 - Math.PI / 2;
        s.x = Math.cos(a) * ring;
        s.y = Math.sin(a) * ring;
    });
    sim.filter((s) => s.node.kind === "container").forEach((s) => {
        const i = index.get(s.node.id)!;
        const anchors = links.filter((l) => l.t === i && sim[l.s].node.kind === "network").map((l) => sim[l.s]);
        const cx = anchors.length ? anchors.reduce((acc, a) => acc + a.x, 0) / anchors.length : 0;
        const cy = anchors.length ? anchors.reduce((acc, a) => acc + a.y, 0) / anchors.length : 0;
        const a = rand() * Math.PI * 2;
        const dist = anchors.length ? 60 + rand() * 60 : ring + 120 + rand() * 80;
        s.x = cx * 1.5 + Math.cos(a) * dist;
        s.y = cy * 1.5 + Math.sin(a) * dist;
    });

    let alpha = 1;
    const alphaDecay = 1 - Math.pow(0.001, 1 / TICKS);
    for (let tick = 0; tick < TICKS; tick++) {
        // repulsion
        for (let i = 0; i < sim.length; i++) {
            const a = sim[i];
            for (let j = i + 1; j < sim.length; j++) {
                const b = sim[j];
                let dx = b.x - a.x, dy = b.y - a.y;
                if (dx === 0 && dy === 0) { dx = rand() - 0.5; dy = rand() - 0.5; }
                const d2 = Math.max(dx * dx + dy * dy, 400);
                if (d2 > 900 * 900) continue;
                const wa = CHARGE[b.node.kind] * alpha / d2;
                const wb = CHARGE[a.node.kind] * alpha / d2;
                a.vx += dx * wa; a.vy += dy * wa;
                b.vx -= dx * wb; b.vy -= dy * wb;
            }
        }
        // springs
        links.forEach(({s, t, d}) => {
            const a = sim[s], b = sim[t];
            const dx = b.x + b.vx - a.x - a.vx, dy = b.y + b.vy - a.y - a.vy;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const k = (dist - d) / dist * alpha / Math.min(degree[s], degree[t]);
            const bias = degree[s] / (degree[s] + degree[t]);
            b.vx -= dx * k * bias; b.vy -= dy * k * bias;
            a.vx += dx * k * (1 - bias); a.vy += dy * k * (1 - bias);
        });
        // gravity towards the host, velocity decay
        sim.forEach((s) => {
            s.vx -= s.x * 0.03 * alpha;
            s.vy -= s.y * 0.03 * alpha;
            if (s.fixed) { s.vx = s.vy = 0; s.x = s.y = 0; return; }
            s.vx *= 0.6; s.vy *= 0.6;
            s.x += s.vx; s.y += s.vy;
        });
        // collision
        for (let i = 0; i < sim.length; i++) {
            const a = sim[i];
            for (let j = i + 1; j < sim.length; j++) {
                const b = sim[j];
                const dx = b.x - a.x, dy = b.y - a.y;
                const min = a.r + b.r;
                const d2 = dx * dx + dy * dy;
                if (d2 >= min * min) continue;
                const d = Math.sqrt(d2) || 1;
                const push = (min - d) / d * 0.5 * 0.8;
                if (!a.fixed) { a.x -= dx * push; a.y -= dy * push; }
                if (!b.fixed) { b.x += dx * push; b.y += dy * push; }
            }
        }
        alpha -= alpha * alphaDecay;
    }

    return Object.fromEntries(sim.map((s) => [s.node.id, {x: s.x, y: s.y}]));
};

// Bounding box of a host's nodes, including labels and room for the box header
export const hostBox = (hostId: string, nodes: GraphNode[], positions: Record<string, Point>,
                        extent: (n: GraphNode) => Extent = nodeExtent): HostBox | null => {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach((n) => {
        const p = positions[n.id];
        if (!p) return;
        const e = extent(n);
        minX = Math.min(minX, p.x - e.x); maxX = Math.max(maxX, p.x + (e.right ?? e.x));
        minY = Math.min(minY, p.y - e.top); maxY = Math.max(maxY, p.y + e.bottom);
    });
    if (!isFinite(minX)) return null;
    const pad = 24, header = 34;
    return {hostId, x: minX - pad, y: minY - pad - header, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2 + header};
};

const GAP = 56;

export type HostPart = { positions: Record<string, Point>, box: HostBox }

// Pack the laid out host clusters into rows
export const packHosts = (parts: HostPart[]): Pick<Layout, "positions" | "width" | "height"> => {
    const area = parts.reduce((acc, p) => acc + p.box.w * p.box.h, 0);
    const rowWidth = Math.max(...parts.map((p) => p.box.w), Math.sqrt(area) * 1.6);
    const positions: Record<string, Point> = {};
    let x = 0, y = 0, rowH = 0, width = 0;
    parts.forEach((p) => {
        if (x > 0 && x + p.box.w > rowWidth) {
            x = 0;
            y += rowH + GAP;
            rowH = 0;
        }
        const dx = x - p.box.x, dy = y - p.box.y;
        Object.entries(p.positions).forEach(([id, pt]) => { positions[id] = {x: pt.x + dx, y: pt.y + dy}; });
        x += p.box.w + GAP;
        rowH = Math.max(rowH, p.box.h);
        width = Math.max(width, x - GAP);
    });
    return {positions, width, height: y + rowH};
};

export const hostIdsOf = (graph: Graph) => graph.nodes.filter((n) => n.kind === "host").map((n) => n.hostId);

export const layoutGraph = (graph: Graph): Layout => {
    const parts = hostIdsOf(graph).map((hostId) => {
        const nodes = graph.nodes.filter((n) => n.hostId === hostId);
        const edges = graph.edges.filter((e) => e.hostId === hostId);
        const positions = layoutHost(nodes, edges);
        return {positions, box: hostBox(hostId, nodes, positions)!};
    });
    return {mode: "graph", ...packHosts(parts)};
};
