import React, { PropsWithChildren, useContext } from "react";
import { useApi } from "@/context/api-context.tsx";

type McpServerContextType = {
    server: McpServer;
    tools: McpServerTool[],
    fetchTools: () => Promise<McpServerTool[]>;
    callTool: (toolName: string, toolArgs?: string[]) => Promise<any>;
}

const McpServerContext = React.createContext<McpServerContextType | null>(null)


export const McpServerProvider = ({ children, server }: PropsWithChildren<{server: McpServer}>) => {
    const { api } = useApi()
    const [tools, setTools] = React.useState<any[]>([])

    const fetchTools = React.useCallback(async () => {
        const response = await api.get(`/api/mcp-servers/${server.name}/tools`)
        setTools(response)
        return response
    }, [api, server.name, setTools])

    const callTool = React.useCallback(async (toolName: string, toolInput?: any) => {
        // @todo lookup tool
        // @todo validate inputs
        return await api.post(`/api/mcp-servers/${server.name}/tools/${toolName}/call`, toolInput)
    }, [api, server.name])

    return (<McpServerContext.Provider value={{server, tools, fetchTools, callTool}}>
        {children}
    </McpServerContext.Provider>)
}

export const useMcpServer = () => {
    const context = useContext(McpServerContext);
    if (!context) {
        throw new Error("useMcpServers must be used within Mcp servers.");
    }
    return context;
}
