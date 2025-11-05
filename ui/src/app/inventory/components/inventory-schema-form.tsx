import React from "react";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";
import ReactJson from "@microlink/react-json-view";

const InventorySchemaForm = () => {
    const {itemType, inputSchema} = useInventory()

    return (
        <div>
            <h2>{itemType}</h2>
            {inputSchema && <Form
                id="inventory-form"
                schema={{
                    version: inputSchema?.version,
                    properties: inputSchema?.properties,
                }}
                uiSchema={{}}
                formData={{}}
                //onSubmit={handleFormSubmit}
                //onChange={handleFormChange}
                validator={validator}
            ></Form>}

            {inputSchema && <ReactJson src={inputSchema} />}
        </div>
    );
};

export default InventorySchemaForm;
