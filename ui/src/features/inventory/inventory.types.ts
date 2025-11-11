import { ColumnDef } from "@tanstack/react-table";

export type InventoryMetadata = {
    item_type: string;
    title: string;
    description?: string;
    icon?: string;
}

export type InventoryItem<T> = {
    item_key: string;
    type: string;
    name: string;
    provider?: string;
    properties: T;
    [key: string]: any; // for any additional properties
}

export type InventoryMetaData = {
    actions?: InventoryActionDef[]
    inputSchema?: object | null
    uiSchema?: object | null
    columns?: ColumnDef<any>[]
    [key: string]: any
}

export type InventoryActionDef = {
    id: string
    name: string
    type?: "form" | "link" | "separator" | "view"
    variant?: "destructive" | "default"
    href?: string
    inputSchema?: object | null
    uiSchema?: object | null
    timeout?: number
}

export type InventoryViewDef = InventoryActionDef

export type Repository = {
    url: string;
}
