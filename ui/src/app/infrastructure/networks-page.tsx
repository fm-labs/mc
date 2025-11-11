import MainContent from "@/components/layout/main-content.tsx";
import { useLoaderData } from "react-router";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import NetworksGrid from "@/app/infrastructure/networks-grid.tsx";
import Header from "@/components/header.tsx";
import OauthMermaid from "@/app/infrastructure/network/oauth-mermaid.tsx";
import OpenidMermaid from "@/app/infrastructure/network/openid-mermaid.tsx";
import OpenidMermaid2 from "@/app/infrastructure/network/openid-mermaid2.tsx";


const NetworksPage = () => {
    const networks: InventoryItem<any>[] = useLoaderData()

    return (
        <MainContent>
            <Header
                title="Infrastructure"
                subtitle={`Manage your infrastructure here.`}>
            </Header>

            <NetworksGrid networks={networks} />
            <OauthMermaid />
            <hr />
            <OpenidMermaid />
            <hr />
            <OpenidMermaid2 />
        </MainContent>
    );
};

export default NetworksPage;
