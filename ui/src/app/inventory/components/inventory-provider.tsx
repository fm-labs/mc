import React, { ReactNode } from "react";
import useDialogState from "@/hooks/use-dialog-state.tsx";
import { useApi } from "@/context/api-context.tsx";
import { ColumnDef } from "@tanstack/react-table";
import { InventoryActionDef, InventoryItem, InventoryMetaData } from "@/features/inventory/inventory.types.ts";
import { DataTableRowAction, DataTableRowActions } from "@/components/data-table/data-table-generic.tsx";
import useDialog from "@/hooks/use-dialog.tsx";
import InventoryActionForm from "@/app/inventory/components/inventory-action-form.tsx";
import { InventoryDialogs } from "@/app/inventory/components/inventory-dialogs.tsx";
import { RJSFSchema } from "@rjsf/utils";
import InventoryViewForm from "@/app/inventory/components/inventory-view-form.tsx";

type InventoryDialogType = "create" | "update" | "delete" | "import"

type InventoryContextType<T> = {
    itemType: string
    inputSchema?: RJSFSchema | null
    columns?: ColumnDef<InventoryItem<T>>[]
    //actions?: InventoryActionDef[]
    metadata?: InventoryMetaData | null
    open: InventoryDialogType | null
    setOpen: (str: InventoryDialogType | null) => void
    items: InventoryItem<T>[]
    setItems: React.Dispatch<React.SetStateAction<T[]>>
    fetchItems: () => Promise<void>
    currentItem: InventoryItem<T> | null
    setCurrentItem: React.Dispatch<React.SetStateAction<InventoryItem<T> | null>>
    dialog: ReactNode
    setDialog: React.Dispatch<React.SetStateAction<ReactNode | undefined>>
    handleAction: (action: InventoryActionDef) => (item: InventoryItem<any>) => Promise<void>
}

export const InventoryContext = React.createContext<InventoryContextType<any> | null>(null);


export function InventoryProvider<T>({ itemType, data, item, children }: {
    itemType: string,
    children: React.ReactNode,
    item?: InventoryItem<any>, // current item
    data?: InventoryItem<T>[]
}) {
    const { api } = useApi();
    const { createDrawer } = useDialog();

    const [open, setOpen] = useDialogState<InventoryDialogType>(null);
    const [items, setItems] = React.useState<InventoryItem<T>[]>(data || []);
    const [currentItem, setCurrentItem] = React.useState<InventoryItem<T> | null>(item || null);
    const [inputSchema, setInputSchema] = React.useState<object | null>(null);
    const [columns, setColumns] = React.useState<any[]>([]);
    //const [actions, setActions] = React.useState<InventoryActionDef[]>([]);
    const [metadata, setMetadata] = React.useState<InventoryMetaData | null>(null);

    const [dialog, setDialog] = React.useState<ReactNode>()

    const fetchItems = React.useCallback(async () => {
        const fetchedData = await api.get(`/api/inventory/${itemType}`);
        console.log("Fetched items for", itemType, fetchedData);
        if (!fetchedData) {
            console.warn("No items found for", itemType);
            return;
        }
        setItems(fetchedData);
    }, [api, itemType, setItems]);

    React.useEffect(() => {
        fetchItems();
    }, [fetchItems]);

    React.useEffect(() => {
        // fetch the schema from the backend
        api.get(`/api/inventory/${itemType}/_schema`).then((schema: any) => {
            console.log("Fetched schema for", itemType, schema);
            if (!schema) {
                console.warn("No schema found for", itemType);
                return;
            }
            setInputSchema(schema);
        }).catch((error: any) => {
            console.error("Error fetching schema for", itemType, error);
        });
    }, [itemType]);

    React.useEffect(() => {
        // fetch the schema from the backend
        api.get(`/api/inventory/${itemType}/_meta`).then((meta: any) => {
            console.log("Fetched meta data for", itemType, meta);
            if (!meta) {
                console.warn("No meta data found for", itemType);
                return;
            }
            setMetadata(meta);
        }).catch((error: any) => {
            console.error("Error fetching meta data for", itemType, error);
        });
    }, [itemType]);

    const handleAction = (def: InventoryActionDef) =>  async (item: InventoryItem<any>) => {
        if (!def || !item) {
            console.warn("No action definition or item provided", def, item);
            return;
        }
        console.log("Handling action", def, "on item", item);

        if (def.type === "form") {
            setDialog(createDrawer({
                children: <InventoryActionForm def={def} item={item}/>,
                onClose: () => setDialog(undefined),
            }))
            return;
        } else if (def.type === "view") {
            setDialog(createDrawer({
                children: <InventoryViewForm def={def} item={item}/>,
                onClose: () => setDialog(undefined),
            }))
            return;
        } else if (def.type === "link") {
            if (def.href) {
                window.location.href = def.href;
                return;
            } else {
                console.warn("No href defined for link action", def);
                alert(`No href defined for link action: ${def.id}`);
            }
        } else if (def.type === "separator") {
            // do nothing
            return;
        } else {
            console.warn("Unknown action", def);
            alert(`Unknown action: ${def.id}`);
        }
    }

    const actions: DataTableRowAction[] = React.useMemo(() => {
        const actionsDef: InventoryActionDef[] = metadata?.actions || [];
        return actionsDef.map((def) => {
            if (def.type==="separator") {
                return { name: "__SEPARATOR__" } as DataTableRowAction;
            }
            return {
                id: def.id,
                name: def.name,
                href: def.href,
                variant: def.variant,
                handler: handleAction(def),
            } as DataTableRowAction;
        });
    }, [metadata?.actions]);

    React.useEffect(() => {
        if (inputSchema && typeof inputSchema==="object" && "properties" in inputSchema) {
            const props = (inputSchema as any).properties;
            const itemCols: ColumnDef<InventoryItem<T>>[] = [
                // {
                //     accessorKey: 'item_key',
                //     header: 'UUID',
                // },
                {
                    accessorKey: "name",
                    header: "name",
                    cell: ({ row }) => {
                        return <span className={"font-bold"} onClick={() => {
                            console.log("Clicked on item name:", row.original);
                            setCurrentItem(row.original);
                            setOpen("update");
                        }}>
                            {row.original.name}
                        </span>;
                    },
                },
            ];
            const propsCols: ColumnDef<InventoryItem<T>>[] = Object.keys(props).map((key, idx) => {
                const isRequired = (inputSchema as any)?.required
                    && Array.isArray((inputSchema as any).required)
                    && (inputSchema as any).required.includes(key);

                return {
                    accessorKey: key,
                    accessorFn: (row: any) => row.properties ? row.properties[key]:undefined,
                    header: key,
                    enableColumnFilter: true,
                    enableHiding: true,
                    meta: { schema: props[key], isProperty: true, keyName: key, hiddenByDefault: idx >= 5 && !isRequired }
                };
            });

            const actionsCol: ColumnDef<InventoryItem<T>> = {
                id: "actions",
                accessorKey: "_actions_",
                header: "Actions",
                cell: ({ row }) => <DataTableRowActions row={row} actions={actions} />,
                enableColumnFilter: false,
                enableSorting: false,
                enableHiding: false,
            };

            setColumns([...itemCols, ...propsCols, actionsCol]);
        }
    }, [inputSchema, actions]);

    const contextValue = {
        itemType,
        inputSchema,
        columns,
        metadata,
        items,
        setItems,
        fetchItems,
        currentItem,
        setCurrentItem,
        open,
        setOpen,
        dialog,
        setDialog,
        handleAction
    };

    return (
        <>
            <InventoryContext value={contextValue}>
                {children}
                <InventoryDialogs />
            </InventoryContext>
        </>
    );
}


// export useInventory hook
export function useInventory<T>() {
    const context = React.useContext(InventoryContext);
    if (!context) {
        throw new Error("useInventory must be used within an InventoryProvider");
    }
    return context as InventoryContextType<T>;
}
