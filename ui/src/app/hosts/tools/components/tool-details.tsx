import * as React from "react";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";
import { IconPlayerPlay, IconPlayerStop, IconBroadcast } from "@tabler/icons-react";

import { Button } from "@/components/ui/button.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card.tsx";
import { Separator } from "@/components/ui/separator.tsx";
import { toast } from "react-toastify";
import { useApi } from "@/context/api-context.tsx";
import { getToolTarget, getToolType, isCmdTool } from "@/app/hosts/tools/components/tool-utils.ts";
import { useTools } from "@/app/hosts/tools/components/tools-provider.tsx";
import { LOCAL_NODE, nodeHeaders } from "@/lib/node-headers.ts";

type ExecOutput = {
    rc: number | null
    stdout: string
    stderr: string
    raw?: any
}

const FORM_ID = "tool-exec-form";

// Normalize POST /tools/{name} response ([rc, stdout, stderr] for cmd tools)
const toExecOutput = (result: ToolExecResult): ExecOutput => {
    if (Array.isArray(result) && result.length === 3) {
        const [rc, stdout, stderr] = result;
        return { rc, stdout: stdout || "", stderr: stderr || "" };
    }
    return { rc: null, stdout: "", stderr: "", raw: result };
};

const OutputBlock = ({ label, children, tone = "default", innerRef }: {
    label: string,
    children: React.ReactNode,
    tone?: "default" | "error",
    innerRef?: React.Ref<HTMLPreElement>,
}) => (
    <div className="space-y-1">
        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
        <pre
            ref={innerRef}
            className={tone === "error"
                ? "max-h-64 overflow-auto rounded-md bg-destructive/10 p-3 font-mono text-xs text-destructive whitespace-pre-wrap break-all"
                : "max-h-[28rem] overflow-auto rounded-md bg-muted p-3 font-mono text-xs whitespace-pre-wrap break-all"}
        >
            {children}
        </pre>
    </div>
);

export function ToolDetails({ tool }: { tool: Tool }) {
    const { api } = useApi();
    const { hostId } = useTools();
    const onNode = hostId !== LOCAL_NODE ? ` on ${hostId}` : "";

    const [formData, setFormData] = React.useState<any>({});
    const [running, setRunning] = React.useState(false);
    const [output, setOutput] = React.useState<ExecOutput | null>(null);
    const [streamLines, setStreamLines] = React.useState<string[] | null>(null);
    const abortRef = React.useRef<AbortController | null>(null);
    // which submit button was used: plain run or live stream
    const submitModeRef = React.useRef<"run" | "stream">("run");
    const logRef = React.useRef<HTMLPreElement | null>(null);

    const hasInputSchema = !!tool.input_schema?.properties && Object.keys(tool.input_schema.properties).length > 0;
    const canStream = isCmdTool(tool);
    const streaming = running && streamLines !== null;

    // abort a running stream when switching tools / leaving the page
    React.useEffect(() => () => abortRef.current?.abort(), []);

    React.useEffect(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, [streamLines]);

    const runTool = async (params: any) => {
        setOutput(null);
        setStreamLines(null);
        setRunning(true);
        const p = api.execTool(tool.name, params || {}, { headers: nodeHeaders(hostId) })
            .then((result: ToolExecResult) => setOutput(toExecOutput(result)))
            .finally(() => setRunning(false));
        await toast.promise(p, {
            pending: `Running ${tool.name}${onNode}...`,
            success: `${tool.name} finished${onNode}`,
            error: {
                render: ({ data }: any) => data?.response?.data?.detail || `Error running ${tool.name}`,
            },
        }).catch(() => undefined);
    };

    const streamTool = async (params: any) => {
        setOutput(null);
        setStreamLines([]);
        setRunning(true);
        const controller = new AbortController();
        abortRef.current = controller;
        let rc: number | null = null;
        try {
            await api.execToolStream(tool.name, params || {}, (ev: ToolStreamEvent) => {
                if (ev.event === "RC") {
                    rc = Number(ev.data);
                    return;
                }
                const line = ev.event === "STDOUT" ? ev.data : `[${ev.event}] ${ev.data}`;
                setStreamLines((prev) => [...(prev || []), line]);
            }, controller.signal, nodeHeaders(hostId));
            setOutput({ rc, stdout: "", stderr: "" });
        } catch (error: any) {
            if (error?.name !== "AbortError") {
                toast.error(error?.message || "Stream failed");
            }
        } finally {
            abortRef.current = null;
            setRunning(false);
        }
    };

    const stopStream = () => abortRef.current?.abort();

    const hasOutput = streamLines !== null || output !== null;

    return (
        <div className="flex min-w-0 flex-col gap-4">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                        {tool.name}
                        <Badge variant="outline" className="font-mono text-xs">{getToolType(tool)}</Badge>
                    </CardTitle>
                    <CardDescription>{tool.description || "No description"}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <pre className="rounded-md bg-muted px-3 py-2 font-mono text-sm whitespace-pre-wrap break-all">
                        <span className="select-none text-muted-foreground">$ </span>{getToolTarget(tool)}
                    </pre>

                    <Separator />

                    <div>
                        {!hasInputSchema && (
                            <p className="mb-2 text-sm text-muted-foreground">This tool takes no parameters.</p>
                        )}
                        <Form
                            id={FORM_ID}
                            schema={hasInputSchema ? tool.input_schema : { type: "object", properties: {} }}
                            formData={formData}
                            onChange={(data) => setFormData(data.formData)}
                            onSubmit={(data) => submitModeRef.current === "stream" ? streamTool(data.formData) : runTool(data.formData)}
                            validator={validator}
                        >
                            {" "}
                        </Form>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        <Button form={FORM_ID} type="submit" disabled={running}
                                onClick={() => { submitModeRef.current = "run"; }}>
                            <IconPlayerPlay size={16} /> Run
                        </Button>
                        {canStream && !streaming && (
                            <Button form={FORM_ID} type="submit" variant="secondary" disabled={running}
                                    onClick={() => { submitModeRef.current = "stream"; }}>
                                <IconBroadcast size={16} /> Run with live output
                            </Button>
                        )}
                        {streaming && (
                            <Button variant="secondary" onClick={stopStream}>
                                <IconPlayerStop size={16} /> Stop
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>

            {hasOutput && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            Output
                            {output?.rc !== null && output?.rc !== undefined && (
                                <Badge variant={output.rc === 0 ? "default" : "destructive"}>exit {output.rc}</Badge>
                            )}
                            {streaming && <Badge variant="outline" className="animate-pulse">streaming</Badge>}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {streamLines !== null && (
                            <OutputBlock label="Live output" innerRef={logRef}>
                                {streamLines.join("\n") || "Waiting for output..."}
                            </OutputBlock>
                        )}
                        {output?.stdout && <OutputBlock label="stdout">{output.stdout}</OutputBlock>}
                        {output?.stderr && <OutputBlock label="stderr" tone="error">{output.stderr}</OutputBlock>}
                        {output?.raw !== undefined && (
                            <OutputBlock label="Response">{JSON.stringify(output.raw, null, 2)}</OutputBlock>
                        )}
                        {output && streamLines === null && !output.stdout && !output.stderr && output.raw === undefined && (
                            <p className="text-sm text-muted-foreground">No output.</p>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
