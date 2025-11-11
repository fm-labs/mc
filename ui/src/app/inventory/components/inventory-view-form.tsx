import React from "react";
import {InventoryViewDef, InventoryItem} from "@/features/inventory/inventory.types.ts";
import {useApi} from "@/context/api-context.tsx";
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import Header from "@/components/header.tsx";
import { Button } from "@/components/ui/button";

const InventoryViewForm = ({def, item}: { def: InventoryViewDef, item: InventoryItem<any> }) => {
    const {itemType, metadata} = useInventory();
    const {api} = useApi()

    const [response, setResponse] = React.useState<any>(null);
    const [loading, setLoading] = React.useState<boolean>(true);

    const fetchView = React.useCallback(async () => {
        try {
            setLoading(true);
            const res = await api.get(`/api/inventory/${itemType}/${item.item_key}/view/${def.id}`);
            setResponse(res);
        } catch (error) {
            console.error("Error fetching view data:", error);
            setResponse({error: "Error fetching view data"});
        } finally {
            setLoading(false);
        }
    }, [api, def.id, item.item_key, itemType]);

    React.useEffect(() => {
        fetchView();
    }, [fetchView]);

    return (
        <div>
            <Header title={`${def.name} ${item.name}`}>
                <Button onClick={fetchView} disabled={loading}>
                    {loading ? "Loading..." : "Refresh"}
                </Button>
            </Header>

            {response && <div className={"mt-2"}>
                <h2>Response:</h2>
                <pre
                    className={"text-xs overflow-auto border font-mono whitespace-pre-wrap break-words"}>{JSON.stringify(response, null, 2)}</pre>
            </div>}
        </div>
    );
};

export default InventoryViewForm;
