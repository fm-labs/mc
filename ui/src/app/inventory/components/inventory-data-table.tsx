import { DataTableGeneric, DataTableProps } from "@/components/data-table/data-table-generic.tsx";
import React from "react";
import { autoColumnsFromData } from "@/components/data-table/data-table-helper.tsx";
import { ColumnDef } from "@tanstack/react-table";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";

interface InventoryDataTableProps<T> extends Omit<DataTableProps<any>, 'columns'> {
    columns?: ColumnDef<T>[];
}

const InventoryDataTable = (props: InventoryDataTableProps<any>) => {
    const { items, columns } = useInventory()

    React.useEffect(() => {
        console.log("Rendering InventoryDataTable with items:", items);
    }, [])

    const _columns = React.useMemo(() => {
        if (props.columns) {
            return props.columns;
        }

        if (!items) {
            console.warn("No items available to generate columns.");
            return [];
        }

        return columns || autoColumnsFromData(items);
    }, [columns, items, props.columns]);

    console.log("Rendering InventoryDataTable with columns:", columns);

    return (
        <>
            {items ? <DataTableGeneric {...props} columns={_columns} data={items} />
                :<p className="text-center">No items found.</p>}
        </>
    );
};

export default InventoryDataTable;
