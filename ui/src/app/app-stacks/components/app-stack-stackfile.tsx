import React from 'react';
import {useApi} from "@/context/api-context.tsx";
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import ReactJson from "@microlink/react-json-view";
import MyForm from "@/components/rjsf/my-form.tsx";
import {toast} from "react-toastify";

const AppStackStackfile = () => {
    const {api} = useApi()
    const { itemType, currentItem } = useInventory<any>()
    const [stackfileContent, setStackfileContent] = React.useState<any>(null);

    const fetchStackfile = React.useCallback(async () => {
        if (!currentItem) {
            return;
        }

        try {
            const response = await api.get(`/api/inventory/${itemType}/${currentItem.id}/view/stackfile`);
            setStackfileContent(response?.content);
        } catch (error) {
            console.error("Error fetching app stack config schema:", error);
        }
    }, [itemType, currentItem])

    React.useEffect(() => {
        fetchStackfile();
    }, [fetchStackfile]);

    return (
        <div>
            <pre className={"max-h-[500px] text-sm overflow-auto"}>{stackfileContent}</pre>
        </div>
    );
};

export default AppStackStackfile;