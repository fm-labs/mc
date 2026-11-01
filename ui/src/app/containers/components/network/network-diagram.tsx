import React from "react";
import {Box, Maximize, Minus, Network, Plus, RotateCcw, Server} from "lucide-react";
import {Button} from "@/components/ui/button.tsx";
import {
    ContainerNode,
    Graph,
    GraphEdge,
    GraphNode,
    NetworkNode,
    networkNodeWidth,
} from "@/app/containers/components/network/network-graph.ts";
import {hostBox, Layout, nodeExtent, Point} from "@/app/containers/components/network/network-layout.ts";
import {TREE, treeExtent} from "@/app/containers/components/network/network-tree-layout.ts";

// ---- colors (hex, readable on light and dark backgrounds) ----

const DRIVER_COLORS: Record<string, string> = {
    bridge: "#3b82f6",
    overlay: "#8b5cf6",
    host: "#f59e0b",
    macvlan: "#14b8a6",
    ipvlan: "#06b6d4",
    null: "#9ca3af",
};
export const driverColor = (driver?: string) => DRIVER_COLORS[driver ?? ""] ?? "#64748b";

const STATE_COLORS: Record<string, string> = {
    running: "#22c55e",
    paused: "#f59e0b",
    restarting: "#ef4444",
    dead: "#ef4444",
};
export const stateColor = (c: ContainerNode) =>
    c.health === "unhealthy" ? "#ef4444" : STATE_COLORS[c.state ?? ""] ?? "#9ca3af";

const PROJECT_PALETTE = ["#6366f1", "#ec4899", "#0ea5e9", "#f97316", "#10b981", "#a855f7", "#eab308", "#e11d48", "#14b8a6", "#84cc16"];
export const projectColor = (project?: string) => {
    if (!project) return undefined;
    let h = 0;
    for (let i = 0; i < project.length; i++) h = (h * 31 + project.charCodeAt(i)) >>> 0;
    return PROJECT_PALETTE[h % PROJECT_PALETTE.length];
};

const truncate = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

// text with a halo in the page background color, so labels stay legible over edges
const haloProps = {stroke: "var(--background)", strokeWidth: 4, paintOrder: "stroke" as const, strokeLinejoin: "round" as const};

type View = { x: number, y: number, k: number }

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

// Polyline with rounded corners, for org-chart connectors
const roundedPath = (pts: [number, number][], r = 8) => {
    if (pts.length < 2) return "";
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 1; i < pts.length - 1; i++) {
        const [px, py] = pts[i - 1], [cx, cy] = pts[i], [nx, ny] = pts[i + 1];
        const inLen = Math.hypot(cx - px, cy - py), outLen = Math.hypot(nx - cx, ny - cy);
        const k = Math.min(r, inLen / 2, outLen / 2);
        if (k < 0.5) { d += ` L${cx},${cy}`; continue; }
        const ax = cx - (cx - px) / inLen * k, ay = cy - (cy - py) / inLen * k;
        const bx = cx + (nx - cx) / outLen * k, by = cy + (ny - cy) / outLen * k;
        d += ` L${ax},${ay} Q${cx},${cy} ${bx},${by}`;
    }
    const [lx, ly] = pts[pts.length - 1];
    return d + ` L${lx},${ly}`;
};

type EdgeGeometry = { d: string, label?: Point }

// Edge path for the force graph: a slight curve so parallel edges stay distinguishable
const graphEdge = (e: GraphEdge, a: Point, b: Point): EdgeGeometry => {
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const dx = b.x - a.x, dy = b.y - a.y;
    const bend = e.kind === "host-network" ? 0 : 0.08;
    const cx = mx - dy * bend, cy = my + dx * bend;
    // IP label 65% of the way towards the container
    const t = 0.65;
    return {
        d: `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`,
        label: {
            x: (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * cx + t * t * b.x,
            y: (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * cy + t * t * b.y,
        },
    };
};

// Edge path for the tree: elbow connectors for tree edges, a soft dashed curve for cross links
const treeEdge = (e: GraphEdge, a: Point, b: Point, cross: boolean): EdgeGeometry => {
    if (cross) {
        // a = network (or the container whose stack is shared), b = container
        const sy = e.kind === "network-container" ? a.y + 20 : a.y;
        return {
            d: `M${a.x},${sy} C${a.x},${sy + 90} ${b.x - 90},${b.y} ${b.x - 18},${b.y}`,
            label: {x: b.x - 52, y: b.y - 9},
        };
    }
    if (e.kind === "host-network") {
        const mid = (a.y + 28 + b.y - 20) / 2;
        return {d: roundedPath([[a.x, a.y + 28], [a.x, mid], [b.x, mid], [b.x, b.y - 20]], 10)};
    }
    if (e.kind === "network-container") {
        const spine = b.x - (TREE.containerInset - TREE.spineInset);
        return {d: roundedPath([[a.x, a.y + 20], [a.x, a.y + 40], [spine, a.y + 40], [spine, b.y], [b.x - 18, b.y]])};
    }
    // shared stack: a = child, b = parent above it
    return {d: roundedPath([[b.x, b.y + 18], [b.x, a.y], [a.x - 18, a.y]])};
};

// ---- nodes ----

const HostShape = ({node, selected}: { node: GraphNode & { kind: "host" }, selected: boolean }) => (
    <g>
        {selected && <rect x={-34} y={-34} width={68} height={68} rx={18} fill="none" stroke="var(--ring)" strokeWidth={3}/>}
        <rect x={-28} y={-28} width={56} height={56} rx={14} fill="var(--primary)"/>
        <Server x={-14} y={-14} width={28} height={28} color="var(--primary-foreground)" strokeWidth={1.75}/>
        <text y={46} textAnchor="middle" fontSize={14} fontWeight={600} fill="var(--foreground)" {...haloProps}>
            {truncate(node.label, 28)}
        </text>
        {node.info?.ServerVersion && (
            <text y={62} textAnchor="middle" fontSize={11} fill="var(--muted-foreground)" {...haloProps}>
                Docker {node.info.ServerVersion}{node.info.OSType ? ` · ${node.info.OSType}` : ""}
            </text>
        )}
    </g>
);

const NetworkShape = ({node, selected}: { node: NetworkNode, selected: boolean }) => {
    const w = networkNodeWidth(node);
    const color = driverColor(node.driver);
    const sub = node.subnets[0] ?? node.driver ?? (node.synthetic ? "network" : "");
    return (
        <g>
            {selected && <rect x={-w / 2 - 5} y={-25} width={w + 10} height={50} rx={25} fill="none" stroke="var(--ring)" strokeWidth={3}/>}
            <rect x={-w / 2} y={-20} width={w} height={40} rx={20}
                  fill="var(--card)" stroke={color} strokeWidth={2}
                  strokeDasharray={node.internal ? "5 3" : undefined}
                  opacity={node.builtin ? 0.85 : 1}/>
            <circle cx={-w / 2 + 20} cy={0} r={13} fill={color} fillOpacity={0.15}/>
            <Network x={-w / 2 + 12} y={-8} width={16} height={16} color={color} strokeWidth={2}/>
            <text x={-w / 2 + 40} y={-2} fontSize={12.5} fontWeight={600}
                  fill={node.builtin ? "var(--muted-foreground)" : "var(--foreground)"}>
                {truncate(node.label, Math.floor((w - 50) / 7))}
            </text>
            <text x={-w / 2 + 40} y={12} fontSize={10} fontFamily="ui-monospace, monospace" fill="var(--muted-foreground)">
                {truncate(sub, Math.floor((w - 50) / 6))}
            </text>
        </g>
    );
};

const ContainerShape = ({node, selected, labelRight, sub}: {
    node: ContainerNode, selected: boolean, labelRight?: boolean, sub?: string
}) => {
    const fill = projectColor(node.project);
    const ring = stateColor(node);
    const active = node.state === "running" || node.state === "paused";
    return (
        <g opacity={active ? 1 : 0.7}>
            {selected && <circle r={22} fill="none" stroke="var(--ring)" strokeWidth={3}/>}
            <circle r={16} fill={fill ?? "var(--muted)"} stroke={ring} strokeWidth={3}/>
            <Box x={-8} y={-8} width={16} height={16} color={fill ? "#fff" : "var(--muted-foreground)"} strokeWidth={2}/>
            {labelRight ? (
                <>
                    <text x={26} y={sub ? -2 : 4} fontSize={12} fontWeight={500} fill="var(--foreground)" {...haloProps}>
                        {truncate(node.label, 24)}
                    </text>
                    {sub && (
                        <text x={26} y={12} fontSize={10} fontFamily="ui-monospace, monospace" fill="var(--muted-foreground)" {...haloProps}>
                            {truncate(sub, 28)}
                        </text>
                    )}
                </>
            ) : (
                <text y={31} textAnchor="middle" fontSize={11.5} fontWeight={500} fill="var(--foreground)" {...haloProps}>
                    {truncate(node.label, 22)}
                </text>
            )}
        </g>
    );
};

// ---- edges ----

const edgeStyle = (e: GraphEdge, nodes: Map<string, GraphNode>, cross: boolean) => {
    if (cross) {
        const net = e.kind === "network-container" ? nodes.get(e.source) as NetworkNode | undefined : undefined;
        return {stroke: net ? driverColor(net.driver) : "var(--muted-foreground)", width: 1.5, dash: "4 4", opacity: 0.45};
    }
    switch (e.kind) {
        case "host-network": {
            const net = nodes.get(e.target) as NetworkNode | undefined;
            return {stroke: "var(--muted-foreground)", width: 2.5, dash: net?.internal ? "6 4" : undefined, opacity: 0.45};
        }
        case "network-container": {
            const net = nodes.get(e.source) as NetworkNode | undefined;
            return {stroke: driverColor(net?.driver), width: 1.75, dash: undefined, opacity: 0.6};
        }
        default:
            return {stroke: "var(--muted-foreground)", width: 1.5, dash: "3 4", opacity: 0.8};
    }
};

// ---- diagram ----

export type NetworkDiagramProps = {
    graph: Graph
    layout: Layout
    selectedId?: string
    onSelect: (id?: string) => void
    search?: string
    className?: string
}

const NetworkDiagram = ({graph, layout, selectedId, onSelect, search, className}: NetworkDiagramProps) => {
    const svgRef = React.useRef<SVGSVGElement>(null);
    const [size, setSize] = React.useState({w: 800, h: 600});
    const [view, setView] = React.useState<View>({x: 0, y: 0, k: 1});
    const [overrides, setOverrides] = React.useState<Record<string, Point>>({});
    const [hoverId, setHoverId] = React.useState<string>();
    const drag = React.useRef<{ kind: "pan" | "node", id?: string, startX: number, startY: number, orig: Point, moved: boolean } | null>(null);

    const tree = layout.mode === "tree";
    const nodeMap = React.useMemo(() => new Map(graph.nodes.map((n) => [n.id, n])), [graph.nodes]);
    const pos = React.useCallback((id: string): Point | undefined => overrides[id] ?? layout.positions[id], [overrides, layout]);

    // neighbours of each node, for hover highlighting
    const neighbours = React.useMemo(() => {
        const m = new Map<string, Set<string>>();
        graph.edges.forEach((e) => {
            (m.get(e.source) ?? m.set(e.source, new Set()).get(e.source)!).add(e.target);
            (m.get(e.target) ?? m.set(e.target, new Set()).get(e.target)!).add(e.source);
        });
        return m;
    }, [graph.edges]);

    React.useEffect(() => {
        const el = svgRef.current;
        if (!el) return;
        const ro = new ResizeObserver(([entry]) => setSize({w: entry.contentRect.width, h: entry.contentRect.height}));
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    const fit = React.useCallback(() => {
        if (!layout.width || !layout.height) return;
        const k = clamp(Math.min(size.w / layout.width, size.h / layout.height) * 0.92, 0.1, 1.4);
        setView({k, x: (size.w - layout.width * k) / 2, y: (size.h - layout.height * k) / 2});
    }, [layout, size]);

    // new layout (structure changed) -> drop manual moves and fit to view
    React.useEffect(() => {
        setOverrides({});
    }, [layout]);
    React.useEffect(() => {
        fit();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [layout, size.w > 0 && size.h > 0]);

    const zoomAt = React.useCallback((px: number, py: number, factor: number) => {
        setView((v) => {
            const k = clamp(v.k * factor, 0.1, 4);
            return {k, x: px - (px - v.x) * (k / v.k), y: py - (py - v.y) * (k / v.k)};
        });
    }, []);

    React.useEffect(() => {
        const el = svgRef.current;
        if (!el) return;
        const onWheel = (ev: WheelEvent) => {
            ev.preventDefault();
            const rect = el.getBoundingClientRect();
            zoomAt(ev.clientX - rect.left, ev.clientY - rect.top, Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0015)));
        };
        el.addEventListener("wheel", onWheel, {passive: false});
        return () => el.removeEventListener("wheel", onWheel);
    }, [zoomAt]);

    const onPointerDown = (ev: React.PointerEvent, nodeId?: string) => {
        if (ev.button !== 0) return;
        ev.stopPropagation();
        (ev.currentTarget as Element).setPointerCapture?.(ev.pointerId);
        drag.current = nodeId
            ? {kind: "node", id: nodeId, startX: ev.clientX, startY: ev.clientY, orig: pos(nodeId) ?? {x: 0, y: 0}, moved: false}
            : {kind: "pan", startX: ev.clientX, startY: ev.clientY, orig: {x: view.x, y: view.y}, moved: false};
    };

    const onPointerMove = (ev: React.PointerEvent) => {
        const d = drag.current;
        if (!d) return;
        const dx = ev.clientX - d.startX, dy = ev.clientY - d.startY;
        if (!d.moved && Math.hypot(dx, dy) < 3) return;
        d.moved = true;
        if (d.kind === "pan") {
            setView((v) => ({...v, x: d.orig.x + dx, y: d.orig.y + dy}));
        } else if (d.id) {
            const id = d.id;
            setOverrides((o) => ({...o, [id]: {x: d.orig.x + dx / view.k, y: d.orig.y + dy / view.k}}));
        }
    };

    const onPointerUp = () => {
        const d = drag.current;
        drag.current = null;
        if (!d || d.moved) return;
        onSelect(d.kind === "node" ? (d.id === selectedId ? undefined : d.id) : undefined);
    };

    // what to emphasise: hovered node, else selected node, plus their neighbours
    const focusId = hoverId ?? selectedId;
    const focus = React.useMemo(() => {
        if (!focusId) return undefined;
        return new Set([focusId, ...(neighbours.get(focusId) ?? [])]);
    }, [focusId, neighbours]);

    const query = search?.trim().toLowerCase();
    const matches = React.useMemo(() => {
        if (!query) return undefined;
        return new Set(graph.nodes.filter((n) => {
            const hay = [n.label, n.kind === "container" ? n.image : undefined, n.kind === "container" ? n.project : undefined,
                ...(n.kind === "container" ? n.attachments.map((a) => a.ipv4) : []), ...(n.kind === "network" ? n.subnets : [])];
            return hay.some((s) => s?.toLowerCase().includes(query));
        }).map((n) => n.id));
    }, [graph.nodes, query]);

    const nodeDim = (id: string) => (focus ? !focus.has(id) : matches ? !matches.has(id) : false);
    const edgeHighlighted = (e: GraphEdge) => !!focusId && (e.source === focusId || e.target === focusId);
    const edgeDim = (e: GraphEdge) => (focus ? !edgeHighlighted(e) : matches ? !(matches.has(e.source) || matches.has(e.target)) : false);

    const boxes = React.useMemo(() => {
        const hostIds = graph.nodes.filter((n) => n.kind === "host").map((n) => n.hostId);
        const current: Record<string, Point> = {...layout.positions, ...overrides};
        const extent = tree ? treeExtent : nodeExtent;
        return hostIds.map((hostId) => hostBox(hostId, graph.nodes.filter((n) => n.hostId === hostId), current, extent)).filter((b) => !!b);
    }, [graph.nodes, layout, overrides, tree]);

    const showIps = view.k >= 1.1;

    // tree: the IP (or image) shown under each container name
    const containerSub = React.useMemo(() => {
        const m = new Map<string, string>();
        if (!tree) return m;
        graph.edges.forEach((e) => {
            if (e.kind === "network-container" && e.ip && layout.edgeRoles?.[e.id] === "tree") m.set(e.target, e.ip);
        });
        graph.nodes.forEach((n) => { if (n.kind === "container" && !m.has(n.id) && n.image) m.set(n.id, n.image); });
        return m;
    }, [graph, layout, tree]);

    // draw order: host-network edges, other edges, then networks, containers and hosts on top
    const order = {network: 0, container: 1, host: 2};
    const sortedNodes = React.useMemo(() => [...graph.nodes].sort((a, b) => order[a.kind] - order[b.kind]), [graph.nodes]);

    return (
        <div className={`relative overflow-hidden rounded-lg border bg-muted/20 ${className ?? ""}`}>
            <svg ref={svgRef} className="size-full touch-none select-none"
                 style={{cursor: drag.current?.kind === "pan" ? "grabbing" : "grab"}}
                 onPointerDown={(ev) => onPointerDown(ev)} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
                 onPointerLeave={() => setHoverId(undefined)}>
                <defs>
                    <pattern id="net-grid" width={24} height={24} patternUnits="userSpaceOnUse"
                             patternTransform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
                        <circle cx={1} cy={1} r={1} fill="var(--muted-foreground)" opacity={0.18}/>
                    </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#net-grid)"/>

                <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
                    {boxes.map((b) => (
                        <g key={b.hostId}>
                            <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={16}
                                  fill="var(--card)" fillOpacity={0.6} stroke="var(--border)" strokeWidth={1.5}/>
                            <text x={b.x + 16} y={b.y + 24} fontSize={12} fontWeight={600} letterSpacing={0.4}
                                  fill="var(--muted-foreground)">
                                {b.hostId.toUpperCase()}
                            </text>
                        </g>
                    ))}

                    {graph.edges.map((e) => {
                        const a = pos(e.source), b = pos(e.target);
                        if (!a || !b) return null;
                        const cross = tree && layout.edgeRoles?.[e.id] !== "tree";
                        const s = edgeStyle(e, nodeMap, cross);
                        const hl = edgeHighlighted(e);
                        const dim = edgeDim(e);
                        // shared-stack edges point child -> parent; draw cross links from the parent
                        const g = tree
                            ? (e.kind === "container-container" && cross ? treeEdge(e, b, a, true) : treeEdge(e, a, b, cross))
                            : graphEdge(e, a, b);
                        // tree edges carry the IP on the container label instead
                        const label = e.ip && g.label && (hl || (!tree && showIps && !dim));
                        return (
                            <g key={e.id} opacity={dim ? 0.08 : 1} className="transition-opacity">
                                <path d={g.d} fill="none"
                                      stroke={s.stroke} strokeWidth={hl ? s.width + 1.25 : s.width}
                                      strokeOpacity={hl ? 1 : s.opacity} strokeDasharray={s.dash}/>
                                {label && (
                                    <text x={g.label!.x} y={g.label!.y} textAnchor="middle" dominantBaseline="middle" fontSize={10}
                                          fontFamily="ui-monospace, monospace" fill="var(--foreground)" {...haloProps}>
                                        {e.ip}
                                    </text>
                                )}
                            </g>
                        );
                    })}

                    {sortedNodes.map((n) => {
                        const p = pos(n.id);
                        if (!p) return null;
                        const selected = n.id === selectedId;
                        return (
                            <g key={n.id} transform={`translate(${p.x} ${p.y})`}
                               opacity={nodeDim(n.id) ? 0.15 : 1} className="cursor-pointer transition-opacity"
                               onPointerDown={(ev) => onPointerDown(ev, n.id)}
                               onPointerEnter={() => !drag.current && setHoverId(n.id)}
                               onPointerLeave={() => !drag.current && setHoverId(undefined)}>
                                {n.kind === "host" && <HostShape node={n} selected={selected}/>}
                                {n.kind === "network" && <NetworkShape node={n} selected={selected}/>}
                                {n.kind === "container" && <ContainerShape node={n} selected={selected} labelRight={tree} sub={containerSub.get(n.id)}/>}
                            </g>
                        );
                    })}
                </g>
            </svg>

            <div className="absolute top-3 right-3 flex flex-col gap-1 rounded-lg border bg-background/90 p-1 shadow-sm backdrop-blur">
                <Button variant="ghost" size="icon" className="size-7" title="Zoom in" onClick={() => zoomAt(size.w / 2, size.h / 2, 1.25)}><Plus/></Button>
                <Button variant="ghost" size="icon" className="size-7" title="Zoom out" onClick={() => zoomAt(size.w / 2, size.h / 2, 0.8)}><Minus/></Button>
                <Button variant="ghost" size="icon" className="size-7" title="Fit to view" onClick={fit}><Maximize/></Button>
                <Button variant="ghost" size="icon" className="size-7" title="Reset node positions"
                        disabled={Object.keys(overrides).length === 0} onClick={() => setOverrides({})}><RotateCcw/></Button>
            </div>

            <Legend graph={graph} tree={tree}/>
        </div>
    );
};

const Legend = ({graph, tree}: { graph: Graph, tree: boolean }) => {
    const drivers = [...new Set(graph.nodes.filter((n): n is NetworkNode => n.kind === "network").map((n) => n.driver ?? "unknown"))];
    const projects = [...new Set(graph.nodes.filter((n): n is ContainerNode => n.kind === "container").map((n) => n.project).filter((p): p is string => !!p))];
    return (
        <div className="absolute bottom-3 left-3 max-w-[calc(100%-1.5rem)] rounded-lg border bg-background/90 px-3 py-2 text-xs shadow-sm backdrop-blur">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
                <span className="font-medium text-muted-foreground">Networks</span>
                {drivers.map((d) => (
                    <span key={d} className="inline-flex items-center gap-1.5">
                        <span className="h-2.5 w-4 rounded-full border-2" style={{borderColor: driverColor(d)}}/>{d}
                    </span>
                ))}
                <span className="inline-flex items-center gap-1.5">
                    <span className="h-2.5 w-4 rounded-full border-2 border-dashed border-muted-foreground"/>internal
                </span>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1.5">
                <span className="font-medium text-muted-foreground">Containers</span>
                {[["running", "#22c55e"], ["paused", "#f59e0b"], ["unhealthy / restarting", "#ef4444"], ["stopped", "#9ca3af"]].map(([label, c]) => (
                    <span key={label} className="inline-flex items-center gap-1.5">
                        <span className="size-3 rounded-full border-[2.5px]" style={{borderColor: c}}/>{label}
                    </span>
                ))}
                <span className="inline-flex items-center gap-1.5">
                    <span className="w-4 border-t-2 border-dotted border-muted-foreground"/>shared network stack
                </span>
                {tree && (
                    <span className="inline-flex items-center gap-1.5">
                        <span className="w-4 border-t-2 border-dashed border-muted-foreground/60"/>also on network
                    </span>
                )}
            </div>
            {projects.length > 0 && (
                <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1.5">
                    <span className="font-medium text-muted-foreground">Compose</span>
                    {projects.slice(0, 10).map((p) => (
                        <span key={p} className="inline-flex items-center gap-1.5">
                            <span className="size-3 rounded-full" style={{backgroundColor: projectColor(p)}}/>{p}
                        </span>
                    ))}
                    {projects.length > 10 && <span className="text-muted-foreground">+{projects.length - 10}</span>}
                </div>
            )}
        </div>
    );
};

export default NetworkDiagram;
