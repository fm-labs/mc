import React from 'react';
import Header from "@/components/header.tsx";
import {InventoryProvider} from "@/app/inventory/components/inventory-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import {Link} from "react-router";
import {Button} from "@/components/ui/button.tsx";
import AppStacksGrid from "@/app/app-stacks/components/app-stacks-grid.tsx";

const AppStacksPage = () => {
    const itemType = "app-stack";
    return (
        <InventoryProvider itemType={itemType}>
            <MainContent>
                <Header
                    title={`My Application Stacks`}
                    subtitle={`Easily manage and deploy your application stacks.`}>

                    <div>
                        <Link to={'portainer'}><Button>Create from template</Button></Link>
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