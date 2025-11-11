import React, {PropsWithChildren} from 'react';
import {InventoryProvider} from "@/app/inventory/components/inventory-provider.tsx";

const AppStacksProvider = ({children}: PropsWithChildren) => {
    return (
        <InventoryProvider itemType={"app-stack"}>
            {children}
        </InventoryProvider>
    );
};

export default AppStacksProvider;