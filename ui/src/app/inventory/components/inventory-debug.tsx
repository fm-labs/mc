import React from 'react';
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import DevOnly from "@/components/dev-only.tsx";
import ReactJson from "@microlink/react-json-view";

const InventoryDebug = () => {
    const {items, columns} = useInventory()

    return (
        <div>
            <DevOnly>
                <h4>Items</h4>
                {items && <ReactJson src={items} collapsed={true} /> }
                <h4>Columns</h4>
                {columns && <ReactJson src={columns} collapsed={true} />}
            </DevOnly>
        </div>
    );
};

export default InventoryDebug;