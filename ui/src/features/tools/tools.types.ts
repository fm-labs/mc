
// Mirrors the backend tool specs in src/mc/plugin/tools/toolindex.py

type ToolSpecBase = {
    name: string;
    description?: string | null;
    input_schema?: any;
    output_schema?: any;
}

type CmdToolSpec = ToolSpecBase & {
    cmd: string;
    args?: string[] | null;
    env?: Record<string, string> | null;
    cwd?: string | null;
}

type HttpToolSpec = ToolSpecBase & {
    url: string;
    method?: string | null;
    data?: string | Record<string, any> | null;
    headers?: Record<string, string> | null;
}

type ToolSpec = CmdToolSpec | HttpToolSpec

type Tool = ToolSpec

// GET /tools returns a map of tool name -> spec
type ToolIndex = Record<string, ToolSpec>

// POST /tools/{name} returns [returncode, stdout, stderr] for cmd tools
type ToolExecResult = [number, string, string] | any

// POST /tools/{name}/stream (format=json) emits one event per line
type ToolStreamEvent = {
    event: "STDOUT" | "RC" | "ERROR" | string;
    data: string;
}
