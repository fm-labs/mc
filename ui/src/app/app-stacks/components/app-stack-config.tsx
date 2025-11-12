import React from 'react';
import {useApi} from "@/context/api-context.tsx";
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import ReactJson from "@microlink/react-json-view";
import MyForm from "@/components/rjsf/my-form.tsx";
import {toast} from "react-toastify";

const AppStackConfig = () => {
    const {api} = useApi()
    const { itemType, currentItem } = useInventory<any>()
    const [configSchema, setConfigSchema] = React.useState<any>(null);

    const fetchConfigSchema = React.useCallback(async () => {
        if (!currentItem) {
            return;
        }

        try {
            const template = await api.get(`/api/inventory/${itemType}/${currentItem.item_key}/view/template`);
            setConfigSchema(template?.environment);
        } catch (error) {
            console.error("Error fetching app stack config schema:", error);
        }
    }, [itemType, currentItem])

    const handleSubmit = async ({ formData }: any) => {
        if (!currentItem) {
            return;
        }

        try {
            console.log("Form submitted with data:", formData);
            const response = await api.post(`/api/inventory/${itemType}/${currentItem.item_key}/action/configure`, {environment: formData});
            console.log("Configuration response:", response);
            toast.success("App stack configuration updated successfully!");
        } catch (error) {
            console.error("Error updating app stack config:", error);
            toast.error("Failed to update app stack configuration.");
        }
    }

    React.useEffect(() => {
        fetchConfigSchema();
    }, [fetchConfigSchema]);

    return (
        <div>
            {/*currentItem ? "Config Schema for " + currentItem.name : "No app stack selected"*/}
            {configSchema && <MyForm schema={configSchema}
                                     formData={currentItem?.properties?.environment}
                                     onSubmit={handleSubmit}/>}
            <ReactJson src={configSchema || {}} collapsed={true} />
        </div>
    );
};

export default AppStackConfig;