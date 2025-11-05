import React from "react";
import NetworkGraph, { EdgeDatum, NodeDatum } from "@/app/aws/components/network-graph.tsx";


const exampleNodes: NodeDatum[] = [
    { id: "A", label: "Alpha", group: 0, size: 10 },
    { id: "B", label: "Beta", group: 1, size: 8 },
    { id: "C", label: "Gamma", group: 1, size: 8 },
    { id: "D", label: "Delta", group: 2, size: 12 },
    { id: "E", label: "Epsilon", group: 2, size: 7 },
];

const exampleEdges: EdgeDatum[] = [
    { source: "A", target: "B", weight: 2 },
    { source: "A", target: "C" },
    { source: "B", target: "D", weight: 3 },
    { source: "C", target: "D" },
    { source: "D", target: "E" },
];

const AwsNetworkGraph = () => {

    const nodes = React.useMemo(() => {
        return exampleNodes
    }, []);

    const edges = React.useMemo(() => {
        return exampleEdges
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Network Graph (TypeScript + D3)</h1>
            <NetworkGraph
                width={960}
                height={600}
                nodes={nodes}
                edges={edges}
                directed
                linkDistance={80}
                collide={1.4}
            />
        </div>


    );
};

export default AwsNetworkGraph;
