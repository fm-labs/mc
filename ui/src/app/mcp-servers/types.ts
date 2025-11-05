
type McpServer = {
    name: string;
    type: "stdio" | "http"
    url?: string;
    command?: string;
    args?: string;
    env?: string
}

type McpServerTool = {
    name: string;
    description?: string;
    title?: string;
    inputSchema?: any
    outputSchema?: any
    icons?: any
    annotations?: any
    _meta?: any
}
