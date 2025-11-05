import { ColumnDef } from "@tanstack/react-table";
import { ArrayCell, ObjectCell } from "./data-table-cells.tsx";

export const autoColumnsFromData = (data: any[]): ColumnDef<any>[] => {
    console.log("AutoColumnsFromData", data);
    if (data.length===0) return [];
    return Object.entries(data[0]).map(([key, value]) => {
        console.log("autocolumn", key, value);
        let column: ColumnDef<any> = {
            accessorKey: key,
            header: key + ":" + (typeof value),
            enableHiding: true,
        };

        if (Array.isArray(value)) {
            column = { ...column, cell: ({ row }) => <ArrayCell value={row.original[key]} /> };
        } else if (typeof value==="object" && value!==null) {
            column = { ...column, cell: ({ row }) => <ObjectCell value={row.original[key]} /> };
        }

        return column;
    });
};

export const autoColumnsFromSchema = (schema: any): ColumnDef<any>[] => {
    if (!schema || !schema.properties) return [];
    return Object.entries(schema.properties).map(([key, value]: [string, any]) => {
        let column: ColumnDef<any> = {
            accessorKey: key,
            header: key + ":" + (value.type || typeof value),
        };

        if (value.type==="array") {
            column = { ...column, cell: ({ row }) => <ArrayCell value={row.original[key]} /> };
        } else if (value.type==="object") {
            column = { ...column, cell: ({ row }) => <ObjectCell value={row.original[key]} /> };
        }

        return column;
    });
};

// Example usage:
// const columns = React.useMemo(() => autoColumnsFromData(data), [data]);
// const columnsFromSchema = React.useMemo(() => autoColumnsFromSchema(schema), [schema]);
