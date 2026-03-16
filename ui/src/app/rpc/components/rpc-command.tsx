import React, { useState } from "react";
import { RJSFSchema } from "@rjsf/utils";
import { useRpcCommand } from "@/app/rpc/components/rpc-command-provider.tsx";
import Header from "@/components/header.tsx";
import { toast } from "sonner";
import ReactJson from "@microlink/react-json-view";
import MyForm from "@/components/rjsf/my-form.tsx";
import {useApi} from "@/context/api-context.tsx";

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


const RpcCommand = () => {
    const { command } = useRpcCommand();
    const { api } = useApi();

    //const initialFormData = {}
    //const [formData, setFormData] = useState<RJSFSchema>(initialFormData);

    const [jsonRpcRequest, setJsonRpcRequest] = useState<JsonRpcRequest>();
    const [jsonRpcResponse, setJsonRpcResponse] = useState<JsonRpcResponse>();
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

    const formId: string = React.useMemo(() => {
        return `rpc-action-form-${command.method}`;
    }, [command.method]);

    const jsonSchema: RJSFSchema = React.useMemo(() => {
        return command?.inputSchema || {};
    }, [command?.inputSchema]);

    const uiSchema: any = React.useMemo(() => {
        return command?.uiSchema || {};
    }, [command?.uiSchema]);

    const handleSubmit = async (data: any): Promise<void> => {
        console.log("handleSubmit", data.formData);
        const jsonRpcReq: JsonRpcRequest = {
            "jsonrpc": "2.0",
            "method": command.method,
            "params": data.formData,
            "id": command?.type==="notification" ? undefined:generateJsonRpcRequestId(),
        };
        setJsonRpcRequest(jsonRpcReq);
        setIsSubmitting(true)
        api.post("/api/rpc", jsonRpcReq, {timeout: 120000}).then((response: JsonRpcResponse) => {
            console.log("JSON RPC RESPONSE", response);
            if (command?.type==="notification") {
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
        })
    };

    // const handleChange = async ({ formData }: any): Promise<void> => {
    //     console.log("handleChange", formData);
    //     setFormData(formData)
    // }

    React.useEffect(() => {
        setJsonRpcRequest(undefined);
        setJsonRpcResponse(undefined);
    }, [command]);

    return (
        <div>
            <Header title={command.method}
                    subtitle={command?.description || "No description available"}>
                {command?.type === "notification" && <span className={"badge badge-secondary"}>Notification</span>}
            </Header>
            <MyForm schema={jsonSchema}
                    uiSchema={uiSchema}
                    id={formId}
                //validator={validator}
                //onChange={handleChange}
                    onSubmit={handleSubmit}
                //showErrorList={"top"}
                //formData={formData}
                //noValidate={true}
            ></MyForm>
            {/*<div className={"my-4 flex justify-end"}>
                <Button form={formId} type="submit">
                    Submit
                </Button>
            </div>*/}

            {isSubmitting && <div className={"my-4"}>
                <span className={"loading loading-spinner"}></span>
                <span className={"ml-2"}>Executing command...</span>
            </div>}
            <div className={"bg-white flex flex-col gap-4 rounded-md"}>
                {jsonRpcRequest && <div>
                    <h3>JSON RPC Request</h3>
                    <ReactJson src={jsonRpcRequest}
                               enableClipboard={true}
                               displayArrayKey={false} displayObjectSize={false} displayDataTypes={false} />
                </div>}
                {jsonRpcResponse && <div>
                    <h3>JSON RPC Response</h3>
                    <ReactJson src={jsonRpcResponse}
                               enableClipboard={true}
                               displayArrayKey={false} displayObjectSize={false} displayDataTypes={false} />
                </div>}
            </div>
        </div>
    );
};

export default RpcCommand;
