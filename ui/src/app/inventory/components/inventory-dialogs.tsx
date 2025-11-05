import { InventoryMutateDrawer } from "@/app/inventory/components/inventory-mutate-drawer.tsx";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";

export function InventoryDialogs() {
    const { open, setOpen, currentItem, dialog } = useInventory();

    if (dialog) {
        return <>{dialog}</>;
    }

    return (
        <>
            <InventoryMutateDrawer
                key="inventory-create"
                open={open==="create"}
                onOpenChange={() => setOpen("create")}
            />

            {/*<InventoryActionDialog
        key='inventory-import'
        open={open === 'import'}
        onOpenChange={() => setOpen('import')}
      />*/}

            {currentItem !== null && (
                <>
                    <InventoryMutateDrawer
                        key={`inventory-update`}
                        open={open==="update"}
                        onOpenChange={() => {
                            setOpen("update");
                            // setTimeout(() => {
                            //   setCurrentRow(null)
                            // }, 500)
                        }}
                        currentRow={currentItem}
                    />
                </>
            )}
        </>
    );
}
