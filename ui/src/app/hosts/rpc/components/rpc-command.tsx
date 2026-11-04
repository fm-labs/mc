import React, { useState } from "react";
import { RJSFSchema } from "@rjsf/utils";
import { IconLoader2, IconPlayerPlay, IconSend } from "@tabler/icons-react";
import { useRpcCommand } from "@/app/hosts/rpc/components/rpc-command-provider.tsx";
import { toast } from "sonner";
import ReactJson from "@microlink/react-json-view";
import MyForm from "@/components/rjsf/my-form.tsx";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card.tsx";
import { Separator } from "@/components/ui/separator.tsx";
import { nodeHeaders } from "@/lib/node-headers.ts";

const generateJsonRpcRequestId = () => {
    return (new Date().getTime() * 1000).toString();
};

type JsonRpcError = {
    code: number;
    message: string;
}

type JsonRpcRequest = {
    jsonrpc: string
    method: string;
    params?: { [key: string]: any };
    id?: string;
}

type JsonRpcResponse = {
    jsonrpc: string;
    result?: any;
    error?: JsonRpcError;
    id?: string;
}

const JsonBlock = ({ label, src }: { label: string, src: object }) => (
    <div className="space-y-1">
        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
        <div className="max-h-[28rem] overflow-auto rounded-md bg-white p-3 text-xs">
            <ReactJson src={src}
                       name={false}
                       enableClipboard={true}
                       displayArrayKey={false} displayObjectSize={false} displayDataTypes={false} />
        </div>
    </div>
);

const RpcCommand = ({ hostId }: { hostId: string }) => {
    const { command } = useRpcCommand();
    const { api } = useApi();

    const [jsonRpcRequest, setJsonRpcRequest] = useState<JsonRpcRequest>();
    const [jsonRpcResponse, setJsonRpcResponse] = useState<JsonRpcResponse>();
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

    const isNotification = command?.type === "notification";
    const formId = `rpc-action-form-${command.method}`;

    const jsonSchema: RJSFSchema = React.useMemo(() => command?.inputSchema || {}, [command]);
    const uiSchema: any = React.useMemo(() => command?.uiSchema || {}, [command]);
    const hasParams = !!jsonSchema?.properties && Object.keys(jsonSchema.properties).length > 0;

    const handleSubmit = async (data: any): Promise<void> => {
        const jsonRpcReq: JsonRpcRequest = {
            "jsonrpc": "2.0",
            "method": command.method,
            "params": data.formData,
            "id": isNotification ? undefined : generateJsonRpcRequestId(),
        };
        setJsonRpcRequest(jsonRpcReq);
        setJsonRpcResponse(undefined);
        setIsSubmitting(true);
        api.post("/api/rpc", jsonRpcReq, {timeout: 120000, headers: nodeHeaders(hostId)})
            .then((response: JsonRpcResponse) => {
            if (isNotification) {
                toast.success("Notification successfully sent.");
            } else {
                if (response?.error) {
                    toast.error(response.error?.message || "Request failed");
                } else {
                    toast.success("Command successfully executed.");
                }
                setJsonRpcResponse(response);
            }
        }).catch((error: any) => {
            toast.error(error?.message || "Something went wrong");
        }).finally(() => {
            setIsSubmitting(false);
        });
    };

    return (
        <div className="flex min-w-0 flex-col gap-4">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="font-mono">{command.method}</span>
                        <Badge variant="outline" className="text-xs">{isNotification ? "notification" : "action"}</Badge>
                    </CardTitle>
                    <CardDescription>{command?.description || "No description available"}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Separator />
                    {!hasParams && (
                        <p className="text-sm text-muted-foreground">This command takes no parameters.</p>
                    )}
                    <MyForm schema={jsonSchema}
                            uiSchema={uiSchema}
                            id={formId}
                            onSubmit={handleSubmit}>
                        <div className="flex flex-wrap gap-2 pt-2">
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting
                                    ? <IconLoader2 size={16} className="animate-spin" />
                                    : isNotification ? <IconSend size={16} /> : <IconPlayerPlay size={16} />}
                                {isSubmitting ? "Executing..." : isNotification ? "Send" : "Execute"}
                            </Button>
                        </div>
                    </MyForm>
                </CardContent>
            </Card>

            {(jsonRpcRequest || jsonRpcResponse) && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            Result
                            {jsonRpcResponse && (
                                <Badge variant={jsonRpcResponse.error ? "destructive" : "default"}>
                                    {jsonRpcResponse.error ? `error ${jsonRpcResponse.error.code}` : "ok"}
                                </Badge>
                            )}
                            {isSubmitting && <Badge variant="outline" className="animate-pulse">running</Badge>}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {jsonRpcRequest && <JsonBlock label="Request" src={jsonRpcRequest} />}
                        {jsonRpcResponse && <JsonBlock label="Response" src={jsonRpcResponse} />}
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default RpcCommand;
