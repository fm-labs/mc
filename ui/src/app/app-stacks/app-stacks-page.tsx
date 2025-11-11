import React from 'react';
import Header from "@/components/header.tsx";
import {InventoryProvider} from "@/app/inventory/components/inventory-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import {ucFirst} from "@/utils/textutil.ts";
import {InventoryPrimaryButtons} from "@/app/inventory/components/inventory-primary-buttons.tsx";
import InventoryDataTable from "@/app/inventory/components/inventory-data-table.tsx";
import DevOnly from "@/components/dev-only.tsx";
import {Link, useLoaderData} from "react-router";
import {Button} from "@/components/ui/button.tsx";
import AppStacksGrid from "@/app/app-stacks/components/app-stacks-grid.tsx";

const AppStacksPage = () => {
    //const data = useLoaderData();

    const itemType = "app-stack";
    return (
        <InventoryProvider itemType={itemType}>
            <MainContent>
                <Header
                    title={`My Application Stacks`}
                    subtitle={`Easily manage and deploy your application stacks.`}>

                    <div>
                        <Link to={'portainer'}><Button>Launch Portainer template</Button></Link>
                    </div>
                </Header>
                {/*<InventorySchemaForm />*/}
                {/*<InventoryDataTable/>*/}
                <AppStacksGrid />
            </MainContent>
        </InventoryProvider>
    );
};

export default AppStacksPage;