import React, { PropsWithChildren, useCallback, useContext } from "react";
import { useApi } from "@/context/api-context.tsx";

type McpServersContextType = {
    servers: McpServer[];
}

const McpServersContext = React.createContext<McpServersContextType | null>(null)


export const McpServersProvider = ({ children }: PropsWithChildren) => {
    const { api } = useApi()
    const [servers, setServers] = React.useState<McpServer[]>([]);

    const fetchServers = useCallback(async () => {
        const response = await api.get("/api/mcp-servers")
        console.log(response)
        setServers(response)
    }, [api, setServers])

    React.useEffect(() => {
        fetchServers()
    }, [fetchServers])

    return (<McpServersContext.Provider value={{servers}}>{children}</McpServersContext.Provider>)
}

export const useMcpServers = () => {
    const context = useContext(McpServersContext);
    if (!context) {
        throw new Error("useMcpServerss must be used within Mcp servers.");
    }
    return context;
}
