import React, {PropsWithChildren} from "react";
import {useApi} from "@/context/api-context.tsx";
import {InventoryItem} from "@/features/inventory/inventory.types.ts";

export type ContainerHost = {
    engine?: string
    url?: string
    autoconnect?: boolean
    connected?: boolean
}

type ContainerHostsContextType = {
    hosts: InventoryItem<ContainerHost>[]
    isHostEnabled: (hostName: string) => boolean
    setHostEnabledState: (hostName: string, state: boolean) => void
}

export const ContainerHostsContext = React.createContext<ContainerHostsContextType | undefined>(undefined);


// The connect/disconnect choice per host is saved in the browser.
// Without a saved choice, the host's "autoconnect" config is used.
export const restoreEnabledState = (hostName: string, fallback: boolean = false): boolean => {
    try {
        const enabledStored = localStorage.getItem(`container_host_${hostName}_enabled`);
        return enabledStored !== null ? JSON.parse(enabledStored) === true : fallback;
    } catch {
        return fallback;
    }
}
const storeEnabledState = (hostName: string, state: boolean) => {
    try {
        localStorage.setItem(`container_host_${hostName}_enabled`, JSON.stringify(state));
    } catch {
        // storage not available, the choice is kept until reload
    }
}

export const ContainerHostsProvider = ({
                                           children,
                                       }: PropsWithChildren) => {
    const {api} = useApi();
    //const [inventory, setInventory] = React.useState<InventoryItem<any>[]>([]);
    const [hosts, setHosts] = React.useState<InventoryItem<ContainerHost>[]>([]);
    const [enabledHosts, setEnabledHosts] = React.useState<Record<string, boolean>>({});

    // const fetchContainerHostsInventory = async () => {
    //     try {
    //         const response = await api.get("/api/inventory/container-host");
    //         setInventory(response);
    //         return response;
    //     } catch (error) {
    //         console.error("Error fetching container host inventory:", error);
    //         return [];
    //     }
    // };

    // shared state, so the sidebar and the host page update together
    const setHostEnabledState = React.useCallback((hostName: string, state: boolean) => {
        storeEnabledState(hostName, state);
        setEnabledHosts((prev) => ({...prev, [hostName]: state}));
    }, []);

    const isHostEnabled = React.useCallback((hostName: string): boolean => {
        if (hostName in enabledHosts) {
            return enabledHosts[hostName];
        }
        const host = hosts.find((h) => h.name === hostName || h.id === hostName);
        return restoreEnabledState(hostName, !!host?.properties?.autoconnect);
    }, [enabledHosts, hosts]);

    const fetchDockerHosts = async (refresh?: boolean) => {
        try {
            const response = await api.get("/api/containers/hosts?" + (refresh ? "refresh=true" : ""));
            setHosts(response);
            return response;
        } catch (error) {
            console.error("Error fetching docker hosts:", error);
            return [];
        }
    };

    React.useEffect(() => {
        fetchDockerHosts(false);
    }, []);

    console.log("Container Hosts Provider", hosts);

    return (
        <ContainerHostsContext.Provider value={{hosts, isHostEnabled, setHostEnabledState}}>
            {children}
        </ContainerHostsContext.Provider>
    );
}

export const useContainerHosts = (): ContainerHostsContextType => {
    const context = React.useContext(ContainerHostsContext);
    if (!context) {
        throw new Error("useContainerHosts must be used within a ContainerHostsProvider");
    }
    return context;
}
