import React from "react";
import { IconServer2 } from "@tabler/icons-react";
import { useApi } from "@/context/api-context.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.tsx";

export const LOCAL_NODE = "localhost";

type HostItem = {
    name: string
    properties?: { engine?: string, url?: string }
}

/**
 * Headers that send a request to another mc node through the node proxy (MC_NODE_PROXY_ENABLED).
 * No header for the local node.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const nodeHeaders = (node?: string | null): Record<string, string> =>
    node && node !== LOCAL_NODE ? { "x-mc-node": node } : {};

/**
 * Lists the nodes the proxy can reach: `docker_hosts` entries with a `node+http(s)://` url.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useProxyNodes = (): string[] => {
    const { api } = useApi();
    const [nodes, setNodes] = React.useState<string[]>([]);

    React.useEffect(() => {
        api.get("/api/containers/hosts")
            .then((hosts: HostItem[]) => setNodes((hosts || [])
                .filter((h) => h.properties?.engine === "node" && /^https?:\/\//.test(h.properties?.url || ""))
                .map((h) => h.name)))
            .catch(() => setNodes([]));
    }, [api]);

    return nodes;
};

/**
 * Picks the node a request runs on. Hidden when no nodes are configured.
 */
export const NodeSelect = ({ value, onChange, disabled }: {
    value: string
    onChange: (node: string) => void
    disabled?: boolean
}) => {
    const nodes = useProxyNodes();

    if (nodes.length === 0) {
        return null;
    }

    return (
        <Select value={value} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger className="w-56" aria-label="Run on node">
                <IconServer2 size={16} />
                <SelectValue />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value={LOCAL_NODE}>{LOCAL_NODE} (this mc)</SelectItem>
                {nodes.map((node) => <SelectItem key={node} value={node}>{node}</SelectItem>)}
            </SelectContent>
        </Select>
    );
};
