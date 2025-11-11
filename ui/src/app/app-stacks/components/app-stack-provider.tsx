import React, {PropsWithChildren} from 'react';
import {InventoryProvider} from "@/app/inventory/components/inventory-provider.tsx";

const AppStackProvider = ({children}: PropsWithChildren<{stack: any}>) => {
    return (
        <>
            {children}
        </>
    );
};

export default AppStackProvider;