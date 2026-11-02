export const isCmdTool = (tool: Tool): tool is CmdToolSpec => "cmd" in tool && !!tool.cmd;

export const isHttpTool = (tool: Tool): tool is HttpToolSpec => "url" in tool && !!tool.url;

export const getToolType = (tool: Tool): "cmd" | "http" | "unknown" =>
    isCmdTool(tool) ? "cmd" : isHttpTool(tool) ? "http" : "unknown";

// Human readable command line / request line for a tool
export const getToolTarget = (tool: Tool): string => {
    if (isCmdTool(tool)) return [tool.cmd, ...(tool.args || [])].join(" ");
    if (isHttpTool(tool)) return `${(tool.method || "GET").toUpperCase()} ${tool.url}`;
    return "";
};
