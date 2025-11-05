import { useMcpServer } from "@/app/mcp-servers/components/mcp-server-provider.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Separator } from "@/components/ui/separator.tsx";
import React, { useState } from "react";
import ReactJson from "@microlink/react-json-view";
import McpServerToolForm from "@/app/mcp-servers/components/mcp-server-tool-form.tsx";

export const McpServer = () => {
    const { server, tools, fetchTools } = useMcpServer();
    const [selectedTool, setSelectedTool] = useState<McpServerTool | null>(null);

    return (<div className={"border p-4 mb-2"}>
        <h3>{server.name}</h3>
        <div className={"flex justify-between"}>
            {server.type==="stdio" && (
                <div>
                    stdio: {server?.command} {server?.args}<br />
                    {server?.env}
                </div>
            )}
            {server.type==="http" && (
                <div>
                    http: {server?.url}<br />
                    {server?.env}
                </div>
            )}
            <div>
                <Button onClick={fetchTools}>List actions</Button>
            </div>
        </div>
        <Separator className={"my-4"} />
        <div>
            {tools && tools.length > 0 && tools.map((tool: McpServerTool) => (
                <div key={tool?.name} className={"mb-2"} onClick={() => setSelectedTool(tool)}>
                    <span className={"font-bold"}>{tool.name}:</span>
                    <p>{tool.description}</p>

                    {selectedTool && selectedTool.name === tool.name && (
                        <>
                            <McpServerToolForm tool={tool} />
                            <ReactJson src={tool} collapsed={true} />
                        </>
                    )}
                </div>
            ))}
        </div>
    </div>);
};
