import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { Download, Maximize2, Pause, Play, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

// -----------------------------
// Types
// -----------------------------
export type GraphData = {
    nodes: {
        id: number;
        item_id: string;
        type: string;
        label: string;
        pos?: [number, number]; // the map position (col, row)
    }[];
    edges: {
        from: number;
        to: number;
        label: string;
    }[];
};

// -----------------------------
// Demo Data (replace with your own)
// -----------------------------
const demoData: GraphData = {
    nodes: [
        { id: 1, item_id: "A", type: "Person", label: "Alice" },
        { id: 2, item_id: "B", type: "Person", label: "Bob" },
        { id: 3, item_id: "C", type: "Company", label: "Acme, Inc." },
        { id: 4, item_id: "D", type: "Tool", label: "Widget" },
        { id: 5, item_id: "E", type: "Location", label: "Vienna", pos: [100, 50] },
    ],
    edges: [
        { from: 1, to: 2, label: "knows" },
        { from: 2, to: 3, label: "works at" },
        { from: 1, to: 3, label: "investor" },
        { from: 3, to: 4, label: "produces" },
        { from: 1, to: 5, label: "lives in" },
        { from: 2, to: 5, label: "visits" },
    ],
};

// -----------------------------
// Helper: color by type
// -----------------------------
const typePalette = d3.scaleOrdinal<string, string>()
    .domain([
        "Person",
        "Company",
        "Tool",
        "Location",
        "Project",
        "Other",
    ])
    .range([
        "#2563eb", // blue
        "#16a34a", // green
        "#9333ea", // purple
        "#dc2626", // red
        "#ca8a04", // amber
        "#64748b", // slate
    ]);

function colorForType(t: string) {
    return typePalette(t) ?? "#64748b";
}

// -----------------------------
// Main Component
// -----------------------------
export default function GraphVisualization({ data }: { data: GraphData }) {
    const [running, setRunning] = useState(true);
    const [filter, setFilter] = useState("");
    const svgRef = useRef<SVGSVGElement | null>(null);
    const gRef = useRef<SVGGElement | null>(null);
    const zoomRef = useRef<d3.ZoomBehavior<Element, unknown> | null>(null);
    const simulationRef = useRef<d3.Simulation<any, undefined> | null>(null);

    // Derived data based on filter
    const { nodes, links } = useMemo(() => {
        const query = filter.trim().toLowerCase();
        if (!query) {
            return {
                nodes: data.nodes.map((n) => ({ ...n })),
                links: data.edges.map((e) => ({ source: e.from, target: e.to, label: e.label })),
            };
        }
        const matchingIds = new Set(
            data.nodes.filter((n) =>
                [n.label, n.type, n.item_id].some((f) => f.toLowerCase().includes(query)),
            ).map((n) => n.id),
        );
        const filteredEdges = data.edges.filter((e) =>
            matchingIds.has(e.from) || matchingIds.has(e.to) || e.label.toLowerCase().includes(query),
        );
        const involvedIds = new Set<number>();
        filteredEdges.forEach((e) => {
            involvedIds.add(e.from);
            involvedIds.add(e.to);
        });
        const filteredNodes = data.nodes.filter((n) => matchingIds.has(n.id) || involvedIds.has(n.id));
        return {
            nodes: filteredNodes.map((n) => ({ ...n })),
            links: filteredEdges.map((e) => ({ source: e.from, target: e.to, label: e.label })),
        };
    }, [data, filter]);

    // Build id -> node lookup for d3
    const nodeById = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
    const d3Links = useMemo(() =>
            links.map((l) => ({
                ...l,
                source: nodeById.get(l.source as number)!,
                target: nodeById.get(l.target as number)!,
            })),
        [links, nodeById]);

    // Simulation setup
    useEffect(() => {
        if (!svgRef.current) return;

        const width = svgRef.current.clientWidth || 900;
        const height = svgRef.current.clientHeight || 600;

        const sim = d3
            .forceSimulation(nodes as any)
            .force("link", d3.forceLink(d3Links as any).id((d: any) => d.id).distance(90).strength(0.15))
            .force("charge", d3.forceManyBody().strength(-120))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius((d: any) => 24))
            .alpha(1)
            .alphaDecay(0.03);

        // Pin nodes with explicit positions (pos = [x,y])
        nodes.forEach((n: any) => {
            if (n.pos) {
                n.fx = n.pos[0];
                n.fy = n.pos[1];
            }
        });

        simulationRef.current = sim;

        const ticked = () => {
            d3.select(gRef.current)
                .selectAll<SVGLineElement, any>("line.link")
                .attr("x1", (d) => (d.source as any).x)
                .attr("y1", (d) => (d.source as any).y)
                .attr("x2", (d) => (d.target as any).x)
                .attr("y2", (d) => (d.target as any).y);

            d3.select(gRef.current)
                .selectAll<SVGTextElement, any>("text.edge-label")
                .attr("x", (d) => ((d.source as any).x + (d.target as any).x) / 2)
                .attr("y", (d) => ((d.source as any).y + (d.target as any).y) / 2);

            d3.select(gRef.current)
                .selectAll<SVGCircleElement, any>("circle.node")
                .attr("cx", (d) => d.x)
                .attr("cy", (d) => d.y);

            d3.select(gRef.current)
                .selectAll<SVGTextElement, any>("text.node-label")
                .attr("x", (d) => d.x)
                .attr("y", (d) => (d.y as number) - 18);
        };

        sim.on("tick", ticked);

        return () => {
            sim.stop();
        };
    }, [nodes.length, d3Links.length]);

    // Zoom / Pan
    useEffect(() => {
        if (!svgRef.current || !gRef.current) return;
        const svg = d3.select(svgRef.current);
        const g = d3.select(gRef.current);

        const zoom = d3
            .zoom<Element, unknown>()
            .scaleExtent([0.3, 3])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });

        zoomRef.current = zoom;
        svg.call(zoom as any);

        return () => {
            svg.on("wheel.zoom", null);
            svg.on("mousedown.zoom", null);
            svg.on("touchstart.zoom", null);
        };
    }, []);

    const handleDrag = d3
        .drag<SVGCircleElement, any>()
        .on("start", (event, d) => {
            if (!event.active) simulationRef.current?.alphaTarget(0.2).restart();
            d.fx = d.x;
            d.fy = d.y;
        })
        .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
        })
        .on("end", (event, d) => {
            if (!event.active) simulationRef.current?.alphaTarget(0);
            // keep node pinned if user dragged while holding Shift
            if (!event.sourceEvent.shiftKey) {
                d.fx = null;
                d.fy = null;
            }
        });

    useEffect(() => {
        if (!gRef.current) return;

        // Definitions (arrowheads & label background filter)
        const defs = d3.select(gRef.current).select("defs");
        if (defs.empty()) {
            const d = d3.select(gRef.current).append("defs");
            d.append("marker")
                .attr("id", "arrow")
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 18)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "#94a3b8");

            const f = d.append("filter").attr("id", "label-bg").attr("x", -0.1).attr("y", -0.1).attr("width", 1.2).attr("height", 1.2);
            f.append("feFlood").attr("flood-color", "white").attr("result", "bg").attr("flood-opacity", 0.9);
            f.append("feComposite").attr("in", "bg").attr("in2", "SourceAlpha").attr("operator", "in");
            f.append("feMerge").selectAll("feMergeNode").data([0, 1]).enter().append("feMergeNode").attr("in", (d, i) => (i===0 ? "bg":"SourceGraphic"));
        }
    }, []);

    // Render nodes & links on data changes
    useEffect(() => {
        const g = d3.select(gRef.current);

        // LINKS
        const linkSel = g.selectAll<SVGLineElement, any>("line.link")
            .data(d3Links, (d: any) => `${(d.source as any).id}-${(d.target as any).id}-${d.label}`);
        linkSel.exit().remove();
        const linkEnter = linkSel
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("stroke", "#cbd5e1")
            .attr("stroke-width", 1.5)
            .attr("marker-end", "url(#arrow)");
        const linksMerged = linkEnter.merge(linkSel as any);

        // EDGE LABELS
        const labelSel = g.selectAll<SVGTextElement, any>("text.edge-label")
            .data(d3Links, (d: any) => `${(d.source as any).id}-${(d.target as any).id}-${d.label}`);
        labelSel.exit().remove();
        const labelEnter = labelSel
            .enter()
            .append("text")
            .attr("class", "edge-label select-none text-xs")
            .attr("text-anchor", "middle")
            .attr("dy", -4)
            .attr("filter", "url(#label-bg)")
            .style("pointer-events", "none")
            .text((d) => '.');
        const labelsMerged = labelEnter.merge(labelSel as any);

        // NODES
        const nodeSel = g.selectAll<SVGCircleElement, any>("circle.node")
            .data(nodes as any, (d: any) => d.id);
        nodeSel.exit().remove();
        const nodeEnter = nodeSel
            .enter()
            .append("circle")
            .attr("class", "node cursor-grab")
            .attr("r", 14)
            .attr("fill", (d) => colorForType((d as any).type))
            .attr("stroke", "white")
            .attr("stroke-width", 2)
            .call(handleDrag as any)
            .on("mouseenter", function() {
                d3.select(this).transition().attr("r", 16);
            })
            .on("mouseleave", function() {
                d3.select(this).transition().attr("r", 14);
            });
        const nodesMerged = nodeEnter.merge(nodeSel as any);

        //NODE LABELS
        const textSel = g.selectAll<SVGTextElement, any>("text.node-label")
            .data(nodes as any, (d: any) => d.id);
        textSel.exit().remove();
        const textEnter = textSel
            .enter()
            .append("text")
            .attr("class", "node-label select-none text-sm font-medium fill-slate-700")
            .attr("text-anchor", "middle")
            .style("pointer-events", "none")
            .text((d: any) => d.type);
        const textsMerged = textEnter.merge(textSel as any);

        // Assign to restart simulation on data change
        simulationRef.current?.nodes(nodes as any);
        (simulationRef.current?.force("link") as d3.ForceLink<any, any>)?.links(d3Links as any);
        simulationRef.current?.alpha(1).restart();

        return () => {
            // nothing to cleanup; elements re-bound on next run
        };
    }, [nodes, d3Links]);

    const handleFit = () => {
        if (!svgRef.current || !gRef.current || !zoomRef.current) return;
        const svg = d3.select(svgRef.current);
        const g = d3.select(gRef.current);

        const bounds = g.node()!.getBBox();
        const fullWidth = svgRef.current.clientWidth;
        const fullHeight = svgRef.current.clientHeight;

        const width = bounds.width;
        const height = bounds.height;
        const midX = bounds.x + width / 2;
        const midY = bounds.y + height / 2;

        if (!width || !height) return;

        const scale = 0.85 / Math.max(width / fullWidth, height / fullHeight);
        const transform = d3.zoomIdentity.translate(fullWidth / 2, fullHeight / 2).scale(scale).translate(-midX, -midY);

        d3.select(svgRef.current).transition().duration(500).call(zoomRef.current.transform as any, transform);
    };

    const handleReset = () => {
        if (!zoomRef.current || !svgRef.current) return;
        d3.select(svgRef.current).transition().duration(400).call(zoomRef.current.transform as any, d3.zoomIdentity);
    };

    const handlePauseResume = () => {
        if (!simulationRef.current) return;
        if (running) {
            simulationRef.current.stop();
            setRunning(false);
        } else {
            simulationRef.current.alpha(0.7).restart();
            setRunning(true);
        }
    };

    const handleExportPNG = async () => {
        if (!svgRef.current) return;
        const svgNode = svgRef.current.cloneNode(true) as SVGSVGElement;
        // remove UI-only stuff like cursor styling
        svgNode.querySelectorAll(".cursor-grab").forEach((n) => n.classList.remove("cursor-grab"));

        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgNode);
        const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);

        const img = new Image();
        const canvas = document.createElement("canvas");
        const bbox = (gRef.current as SVGGElement).getBBox();
        const padding = 32;
        const w = Math.max(800, bbox.width + padding * 2);
        const h = Math.max(600, bbox.height + padding * 2);
        canvas.width = w;
        canvas.height = h;

        img.onload = () => {
            const ctx = canvas.getContext("2d")!;
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, w, h);
            // Draw centered
            const temp = document.createElement("canvas");
            temp.width = img.width;
            temp.height = img.height;
            const tctx = temp.getContext("2d")!;
            tctx.drawImage(img, 0, 0);
            ctx.drawImage(temp, padding, padding);

            const a = document.createElement("a");
            a.download = "graph.png";
            a.href = canvas.toDataURL("image/png");
            a.click();
            URL.revokeObjectURL(url);
        };
        img.src = url;
    };

    const handleZoom = (dir: 1 | -1) => {
        if (!zoomRef.current || !svgRef.current) return;
        const svg = d3.select(svgRef.current);
        svg.transition().duration(200).call(zoomRef.current.scaleBy as any, dir > 0 ? 1.2:0.8);
    };

    return (
        <div className="w-full h-full p-4">
            <Card className="w-full h-[80vh] shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-xl">Graph Visualization</CardTitle>
                    <div className="flex items-center gap-2">
                        <div className="hidden md:flex items-center gap-2">
                            <Button variant="secondary" onClick={() => handleZoom(1)} title="Zoom in"><ZoomIn
                                className="w-4 h-4" /></Button>
                            <Button variant="secondary" onClick={() => handleZoom(-1)} title="Zoom out"><ZoomOut
                                className="w-4 h-4" /></Button>
                            <Button variant="secondary" onClick={handleFit} title="Fit to view"><Maximize2
                                className="w-4 h-4" /></Button>
                            <Button variant="secondary" onClick={handleReset} title="Reset view"><RotateCcw
                                className="w-4 h-4" /></Button>
                            <Button variant="secondary" onClick={handlePauseResume}
                                    title={running ? "Pause layout":"Resume layout"}>
                                {running ? <Pause className="w-4 h-4" />:<Play className="w-4 h-4" />}
                            </Button>
                            <Button variant="secondary" onClick={handleExportPNG} title="Export PNG"><Download
                                className="w-4 h-4" /></Button>
                        </div>
                        <Input
                            placeholder="Filter by label, type, or item id…"
                            className="w-64"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        />
                    </div>
                </CardHeader>
                <CardContent className="w-full h-[68vh]">
                    <svg ref={svgRef} className="w-full h-full bg-white rounded-2xl shadow-inner">
                        <g ref={gRef}>
                            {/* defs are inserted via d3 in effect */}
                        </g>
                    </svg>
                    <div className="text-xs text-slate-500 mt-2">
                        Tip: Drag nodes to reposition. Hold <kbd
                        className="px-1 py-0.5 rounded bg-slate-100 border">Shift</kbd> while releasing to keep them
                        pinned. Use the search box to filter.
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
