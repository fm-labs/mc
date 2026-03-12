import React from "react";
import { Button } from "@/components/ui/button.tsx";
import {
    Sheet,
    SheetClose,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet.tsx";
import { Form } from "@rjsf/shadcn";
import validator from "@rjsf/validator-ajv8";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { useApi } from "@/context/api-context.tsx";
import { toast } from "react-toastify";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";
import { RJSFSchema } from "@rjsf/utils";
import ReactJson from "@microlink/react-json-view";

type InventoryMutateDrawerProps = {
    open: boolean
    onOpenChange: (open: boolean) => void
    currentRow?: InventoryItem<any>
}

export function InventoryMutateDrawer({
                                          open,
                                          onOpenChange,
                                          currentRow,
                                      }: InventoryMutateDrawerProps) {
    const { itemType, inputSchema, fetchItems } = useInventory();
    const { api } = useApi();
    const isUpdate = !!currentRow;

    const handleFormSubmit = async (data: any) => {
        // handle form submission
        console.log("Form submitted:", data.formData);
        //onOpenChange(false);
        let p;
        if (isUpdate) {
            const updatedItem = { ...currentRow, properties: data.formData };
            console.log("Updating item with data:", updatedItem);
            p = api.updateInventoryItem(itemType, updatedItem);
        } else {
            const newItem = { name: data.formData.name, properties: data.formData };
            p = api.createInventoryItem(itemType, newItem);
        }
        await toast.promise(p, {
            pending: isUpdate ? "Updating item...":"Creating item...",
            success: isUpdate ? "Item updated!":"Item created!",
            error: isUpdate ? "Error updating item":"Error creating item",
        }).then(() => {
            fetchItems();
            onOpenChange(false);
        });
    };

    const handleFormChange = (data: any) => {
        // handle form submission
        console.log("Form changed:", data.formData);
        //onOpenChange(false);
    };

    const schema: RJSFSchema = React.useMemo(() => {
        //const _propertiesSchema: any = inputSchema || {"type": "object", "properties": {}, "required": []};
        // const _schema: RJSFSchema = {
        //     "type": "object",
        //     "properties": _propertiesSchema,
        //     "required": []
        // }
        // console.log("Computed schema:", _schema);
        //
        // const isSchemaValid = validator.isValid(_schema, {}, {});
        // if (!isSchemaValid) {
        //     console.error("Invalid schema:", _schema);
        //
        //     const errors = validator.rawValidation(_schema, {});
        //     console.error("Schema validation errors:", errors);
        //
        //     return {"type": "object", "properties": {}};
        // }
        const _properties: any = {
            name: { type: "string", "description": "Unique Name of the inventory item" },
            ...inputSchema?.properties,
        };
        const _schema: RJSFSchema = {
            type: "object",
            properties: _properties,
            required: inputSchema?.required || [],
        };
        return _schema;
    }, [inputSchema]);

    if (!itemType || !inputSchema) {
        return null;
    }

    return (
        <Sheet
            open={open}
            onOpenChange={(v) => {
                onOpenChange(v);
            }}
        >
            <SheetContent className="flex flex-col overflow-y-scroll">
                <SheetHeader className="text-start">
                    <SheetTitle>{isUpdate ? "Update":"Create"} {itemType} Inventory</SheetTitle>
                    <SheetDescription>
                        {isUpdate
                            ? "Update the repo by providing necessary info."
                            :"Add a new repo by providing necessary info."}
                        Click save when you&apos;re done.
                    </SheetDescription>
                </SheetHeader>
                <div className={"px-4"}>
                    <Form
                        id="inventory-form"
                        schema={schema}
                        uiSchema={{}}
                        formData={currentRow?.properties || {}}
                        onSubmit={handleFormSubmit}
                        onChange={handleFormChange}
                        validator={validator}
                    >{" "}</Form>
                    <hr />
                    {currentRow!==undefined && <div className={"px-4 max-h-96 overflow-y-auto"}>
                        <ReactJson src={currentRow}
                                   collapsed={true}
                                   displayDataTypes={false}
                                   displayObjectSize={false} />
                    </div>}
                </div>
                <SheetFooter className="gap-2">
                    <SheetClose asChild>
                        <Button variant="outline">Close</Button>
                    </SheetClose>
                    <Button form="inventory-form" type="submit">
                        Save changes
                    </Button>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
