import React, { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";

// ---- Types ----
export type NodeDatum = {
    id: string;
    label?: string;
    group?: string | number;
    size?: number; // relative size
};

export type EdgeDatum = {
    id?: string;
    source: string; // node id
    target: string; // node id
    weight?: number; // thickness
};

export type NetworkGraphProps = {
    width?: number;
    height?: number;
    nodes: NodeDatum[];
    edges: EdgeDatum[];
    /** If true, show directional arrows */
    directed?: boolean;
    /** Strength of link distance; lower is longer links */
    linkDistance?: number;
    /** Collision radius multiplier, 0 to disable */
    collide?: number;
};

// ---- Component ----
const NetworkGraph: React.FC<NetworkGraphProps> = ({
                                                       width = 900,
                                                       height = 600,
                                                       nodes,
                                                       edges,
                                                       directed = true,
                                                       linkDistance = 60,
                                                       collide = 1.2,
                                                   }) => {
    const svgRef = useRef<SVGSVGElement | null>(null);
    const gRef = useRef<SVGGElement | null>(null);
    const simRef = useRef<d3.Simulation<any, undefined> | null>(null);

    const [hover, setHover] = useState<{
        x: number;
        y: number;
        node?: NodeDatum;
    } | null>(null);

    // Create internal copies so d3 can mutate x/y/vx/vy
    const data = useMemo(() => {
        const idToNode = new Map(nodes.map((n) => [n.id, { ...n }]));
        const simNodes: (NodeDatum & { x?: number; y?: number })[] = nodes.map(
            (n) => ({ ...n })
        );
        const simLinks = edges.map((l) => ({ ...l }));

        // Validate links reference existing nodes
        for (const l of simLinks) {
            if (!idToNode.has(l.source) || !idToNode.has(l.target)) {
                console.warn("Link references missing node:", l);
            }
        }
        return { nodes: simNodes, links: simLinks };
    }, [nodes, edges]);

    // Build a color scale for groups
    const color = useMemo(() => d3.scaleOrdinal(d3.schemeTableau10), []);

    // Setup once
    useEffect(() => {
        const svg = d3.select(svgRef.current!);
        const g = d3.select(gRef.current!);

        // Zoom / pan
        const zoomed = (event: d3.D3ZoomEvent<Element, unknown>) => {
            g.attr("transform", event.transform.toString());
        };
        const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.1, 5]).on("zoom", zoomed);
        svg.call(zoom as any);

        // Define arrowhead marker once
        if (directed) {
            const defs = svg.select("defs").empty() ? svg.append("defs") : svg.select("defs");
            defs
                .append("marker")
                .attr("id", "arrowhead")
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 14)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("opacity", 0.7);
        }

        return () => {
            svg.on("wheel.zoom", null);
            (svg as any).on("mousedown.zoom", null);
        };
    }, [directed]);

    // (Re)start simulation whenever data changes
    useEffect(() => {
        const sim = d3
            .forceSimulation(data.nodes as any)
            .force(
                "link",
                d3
                    .forceLink(data.links as any)
                    .id((d: any) => d.id)
                    .distance(linkDistance)
                    .strength(0.5)
            )
            .force("charge", d3.forceManyBody().strength(-80))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .alphaDecay(0.05);

        // if (collide > 0) {
        //     sim.force(
        //         "collide",
        //         d3.forceCollide<NodeDatum>((d) => (d.size ? d.size : 6) * collide)
        //     );
        // }

        simRef.current = sim as any;

        //const svg = d3.select(svgRef.current!);
        const g = d3.select(gRef.current!);

        // ----- Links -----
        const linkSel = g
            .selectAll<SVGLineElement, any>("line.link")
            .data(data.links, (d: any) => d.id ?? `${d.source}->${d.target}`);

        linkSel.exit().remove();

        const linkEnter = linkSel
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("stroke", "currentColor")
            .attr("stroke-opacity", 0.2)
            .attr("stroke-width", (d) => Math.max(1, d.weight ?? 1));

        const linksMerged = linkEnter.merge(linkSel as any);

        if (directed) {
            linksMerged.attr("marker-end", "url(#arrowhead)");
        } else {
            linksMerged.attr("marker-end", null);
        }

        // ----- Nodes -----
        const nodeSel = g
            .selectAll<SVGGElement, any>("g.node")
            .data(data.nodes, (d: any) => d.id);

        nodeSel.exit().remove();

        const nodeEnter = nodeSel
            .enter()
            .append("g")
            .attr("class", "node")
            .style("cursor", "grab")
            .call(
                d3
                    .drag<SVGGElement, NodeDatum>()
                    .on("start", (event, d: any) => {
                        if (!event.active) (simRef.current as any)?.alphaTarget(0.3).restart();
                        d.fx = d.x;
                        d.fy = d.y;
                    })
                    .on("drag", (event, d: any) => {
                        d.fx = event.x;
                        d.fy = event.y;
                    })
                    .on("end", (event, d: any) => {
                        if (!event.active) (simRef.current as any)?.alphaTarget(0);
                        d.fx = null;
                        d.fy = null;
                    })
            );

        nodeEnter
            .append("circle")
            .attr("r", (d) => (d.size ? d.size : 6))
            .attr("fill", (d) => (d.group ? (color(d.group.toString()) as string) : (color("default") as string)))
            .attr("fill-opacity", 0.9)
            .attr("stroke", "#111")
            .attr("stroke-opacity", 0.4);

        nodeEnter
            .append("text")
            .attr("x", 10)
            .attr("y", 4)
            .attr("font-size", 12)
            .attr("opacity", 0.8)
            .text((d) => d.label ?? d.id);

        const nodesMerged = nodeEnter.merge(nodeSel as any);

        // Hover interaction for tooltip
        nodesMerged
            .on("mouseenter", (event: any, d: NodeDatum & { x?: number; y?: number }) => {
                const pt = d3.pointer(event, svgRef.current);
                setHover({ x: pt[0], y: pt[1], node: d });
            })
            .on("mousemove", (event: any, d: NodeDatum & { x?: number; y?: number }) => {
                const pt = d3.pointer(event, svgRef.current);
                setHover({ x: pt[0], y: pt[1], node: d });
            })
            .on("mouseleave", () => setHover(null));

        // Tick update
        sim.on("tick", () => {
            linksMerged
                .attr("x1", (d: any) => (typeof d.source === "object" ? d.source.x : (data.nodes.find((n) => n.id === d.source) as any)?.x))
                .attr("y1", (d: any) => (typeof d.source === "object" ? d.source.y : (data.nodes.find((n) => n.id === d.source) as any)?.y))
                .attr("x2", (d: any) => (typeof d.target === "object" ? d.target.x : (data.nodes.find((n) => n.id === d.target) as any)?.x))
                .attr("y2", (d: any) => (typeof d.target === "object" ? d.target.y : (data.nodes.find((n) => n.id === d.target) as any)?.y));

            nodesMerged.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
        });

        return () => {
            sim.stop();
        };
    }, [data, width, height, linkDistance, collide, directed, color]);

    // --- Render ---
    return (
        <div className="w-full h-full relative">
            <svg
                ref={svgRef}
                width={width}
                height={height}
                viewBox={`0 0 ${width} ${height}`}
                className="bg-white text-neutral-700 rounded-2xl shadow border border-neutral-200"
            >
                <defs />
                <g ref={gRef} />
            </svg>

            {/* Tooltip */}
            {hover?.node && (
                <div
                    className="pointer-events-none absolute px-3 py-2 rounded-xl shadow text-sm bg-white/90 border border-neutral-200"
                    style={{ left: hover.x + 12, top: hover.y + 12 }}
                >
                    <div className="font-medium">{hover.node.label ?? hover.node.id}</div>
                    {hover.node.group !== undefined && (
                        <div className="opacity-70">Group: {String(hover.node.group)}</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default NetworkGraph;
