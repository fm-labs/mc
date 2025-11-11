import React from 'react';
import {InventoryActionDef, InventoryItem} from "@/features/inventory/inventory.types.ts";
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import {Button} from "@/components/ui/button.tsx";

const InventoryItemActionButtons = ({item}: { item: InventoryItem<any>}) => {
    const {metadata, handleAction} = useInventory();
    const actionsDef: InventoryActionDef[] = metadata?.actions || [];

    return (
        <div className={"flex gap-x-1"}>
            {actionsDef.map((def) => {
            if (def.type === "separator") {
                return <></>
            }
            return <Button key={def.name} variant={"outline"} size={"sm"} onClick={() => handleAction(def)(item)}>{def.name}</Button>
        })}
        </div>
    );
};

export default InventoryItemActionButtons;