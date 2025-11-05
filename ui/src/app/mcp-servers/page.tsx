import React from "react";
import Header from "@/components/header.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import { McpServerProvider } from "@/app/mcp-servers/components/mcp-server-provider.tsx";
import { McpServersProvider, useMcpServers } from "@/app/mcp-servers/components/mcp-servers-provider.tsx";
import { McpServer } from "@/app/mcp-servers/components/mcp-server.tsx";
import { Link } from "react-router";

const McpServers = () => {
    const { servers } = useMcpServers();
    return <div>
        {servers.length > 0 && servers.map((server: McpServer) => (
            <McpServerProvider key={server.name} server={server}>
                <McpServer />
            </McpServerProvider>
        ))}
    </div>;
};

const McpServersPage = () => {
    return (
        <MainContent>
            <Header title="MCP Servers" subtitle="Manage your MCP Servers here">
                <Link to="docker">View Docker MCP Catalog</Link>
            </Header>
            <McpServersProvider>
                <McpServers />
            </McpServersProvider>
        </MainContent>
    );
};

export default McpServersPage;
