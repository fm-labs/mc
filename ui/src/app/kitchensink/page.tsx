import { KitchensinkProvider } from "@/app/kitchensink/components/kitchensink-provider.tsx";
import KitchensinkInventoryItems from "@/app/kitchensink/components/kitchensink-inventory-items.tsx";
import { InventoryProvider } from "@/app/inventory/components/inventory-provider.tsx";
import { useApi } from "@/context/api-context.tsx";
import * as React from "react";
import { InventoryMetadata } from "@/features/inventory/inventory.types.ts";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
//import styled from "@emotion/styled";

//const INVENTORY_ITEM_TYPES = ["host", "dns-domain", "container-image", "repository", "cloud"];

// const MasonryOuter = styled.div`
//     display: flex;
//     flex-direction: column;
//
//     .masonry-grid {
//         display: flex;
//         width: auto;
//     }
//
//     .masonry-grid-col section {
//         margin: 0;
//     }
// `;
//
// const MasonryContent = styled.section`
//     display: grid;
//     //grid-auto-flow: dense;
//     //grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
//     //gap: 1rem;
//     margin: auto;
//     //width: 95vw;
//     //width: calc(100% - 2rem);
//     //padding-bottom: 1rem;
// `;

const KitchensinkPage = () => {
    const { api } = useApi();
    const [metadata, setMetadata] = React.useState<InventoryMetadata[]>([]);

    const fetchInventoryMetadata = React.useCallback(async (): Promise<InventoryMetadata[]> => {
        try {
            const response = await api.get("/api/inventory");
            console.log("response", response);
            return response;
        } catch (error) {
            console.error("Error fetching inventory metadata:", error);
            throw error;
        }
    }, [api]);

    React.useEffect(() => {
        fetchInventoryMetadata().then(data => {
            console.log("Inventory metadata:", data);
            if (data) {
                setMetadata(data);
            }
        });
    }, []);

    return (
        <KitchensinkProvider>
            <MainContent>
                <Header title={"Kitchensink"} subtitle={"List of all inventory items"}></Header>
                {metadata && metadata.map((item: InventoryMetadata) => {
                    return (
                        <InventoryProvider itemType={item.item_type} key={item.item_type}>
                            <KitchensinkInventoryItems />
                        </InventoryProvider>
                    );
                })}

            </MainContent>
        </KitchensinkProvider>
    );
};

export default KitchensinkPage;
