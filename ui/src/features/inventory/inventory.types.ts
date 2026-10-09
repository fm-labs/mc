export type InventoryMetadata = {
    item_type: string;
    title: string;
    description?: string;
    icon?: string;
}

export type InventoryItem<T> = {
    id: string;
    type: string;
    properties: T;
    [key: string]: any; // for any additional properties
}

export type InventoryMetaData = {
    index?: InventoryIndexDef
    actions?: InventoryActionDef[]
    inputSchema?: object | null
    uiSchema?: object | null
    [key: string]: any
}

// table config of the inventory index page
export type InventoryIndexDef = {
    columns?: InventoryColumnDef[]
}

export type InventoryColumnDef = {
    name: string   // "id" or a property name
    title?: string // header label, defaults to the name
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
