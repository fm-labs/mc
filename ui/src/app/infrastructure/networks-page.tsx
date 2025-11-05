import MainContent from "@/components/layout/main-content.tsx";
import { useLoaderData } from "react-router";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import NetworksGrid from "@/app/infrastructure/networks-grid.tsx";
import Header from "@/components/header.tsx";
import OauthMermaid from "@/app/infrastructure/network/oauth-mermaid.tsx";


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
        </MainContent>
    );
};

export default NetworksPage;
