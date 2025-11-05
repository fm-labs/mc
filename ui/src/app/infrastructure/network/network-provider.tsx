import React from "react";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { useApi } from "@/context/api-context.tsx";


type NetworkContextType = {
    network: InventoryItem<any>;
    hosts: InventoryItem<any>[];
    setHosts: (hosts: InventoryItem<any>[]) => void;
}

const NetworkContext = React.createContext<NetworkContextType | null>(null);

export function NetworkProvider({ children, network }: { children: React.ReactNode, network: InventoryItem<any> }) {
    const { api } = useApi()
    const [hosts, setHosts] = React.useState<InventoryItem<any>[]>([]);

    const fetchHosts = React.useCallback(() => {
        api.get(`/api/inventory/host/?network_name=${network.name}`).then((data: any) => {
            const _filtered= data.filter((item: any) => item?.properties?.network === network.name);
            setHosts(_filtered || []);
        })
    }, [api, setHosts, network.name])

    React.useEffect(() => {
        fetchHosts()
    }, [])

    return (
        <NetworkContext value={{network, hosts, setHosts}}>
            {children}
        </NetworkContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useNetwork = () => {
    const reposContext = React.useContext(NetworkContext);

    if (!reposContext) {
        throw new Error("useNetwork has to be used within <NetworkContext>");
    }

    return reposContext;
};
