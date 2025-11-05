import React from "react";
import { DockerMcpCatalogProvider } from "@/app/mcp-servers/components/docker-mcp-catalog-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import DockerMcpCatalog from "@/app/mcp-servers/components/docker-mcp-catalog.tsx";

const DockerCatalogPage = () => {
    return (
        <MainContent>
            <Header title="Docker MCP Catalog"
                    subtitle="Docker wrapper mcp servers" />
            <DockerMcpCatalogProvider>
                <DockerMcpCatalog />
            </DockerMcpCatalogProvider>
        </MainContent>
    );
};

export default DockerCatalogPage;
