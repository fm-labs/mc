import React, { createContext, useContext } from "react";
import { AwsInventoryFilter, AwsInventoryItemFull } from "@/app/aws/types.ts";
import { useApi } from "@/context/api-context.tsx";

type AwsInventoryContextType = {
    items: AwsInventoryItemFull[],
    filter: AwsInventoryFilter,
    fetchItems: () => Promise<void>
}


const AwsInventoryContext = createContext<AwsInventoryContextType | null>(null);

const defaultFilter: AwsInventoryFilter = {
    accountIds: [],
    regionIds: [],
    serviceIds: [],
    resourceTypes: [],
    properties: {}
};

export function AwsInventoryProvider({ children, filter }: { children: React.ReactNode, filter?: Partial<AwsInventoryFilter> }) {
    const { api } = useApi();
    const [items, setItems] = React.useState<AwsInventoryItemFull[]>([]);

    const _filter = { ...defaultFilter, ...filter };
    console.log(_filter);

    const fetchItems = React.useCallback(async () => {
        try {
            const queryParams = new URLSearchParams();
            if (_filter.accountIds.length > 0) {
                queryParams.append("account_id", _filter.accountIds.join(","));
            }
            if (_filter.regionIds.length > 0) {
                queryParams.append("region_id", _filter.regionIds.join(","));
            }
            if (_filter.serviceIds.length > 0) {
                queryParams.append("service_id", _filter.serviceIds.join(","));
            }
            if (_filter.resourceTypes.length > 0) {
                queryParams.append("resource_type", _filter.resourceTypes.join(","));
            }
            if (_filter.properties && Object.keys(_filter.properties).length > 0) {
                queryParams.append("properties", JSON.stringify(_filter.properties));
            }

            const url = `/api/aws/inventory?${queryParams.toString()}`;
            console.log("Fetching data from:", url);
            const response = await api.get(url);
            console.log("Data fetched:", response);
            setItems(response);
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [api, setItems]);

    React.useEffect(() => {
        fetchItems();
    }, [fetchItems]);

    return (
        <AwsInventoryContext.Provider value={{ items, filter: _filter, fetchItems }}>
            {children}
        </AwsInventoryContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAwsInventory = () => {
    const context = useContext(AwsInventoryContext);

    if (!context) {
        throw new Error("useAwsInventory has to be used within <AwsInventoryProvider>");
    }

    return context;
}
