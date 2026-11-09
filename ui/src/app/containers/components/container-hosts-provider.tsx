import React, {PropsWithChildren} from "react";
import {useApi} from "@/context/api-context.tsx";
import {InventoryItem} from "@/features/inventory/inventory.types.ts";

export type ContainerHost = {
    engine?: string
    url?: string
    autoconnect?: boolean
    connected?: boolean
}

/** Connection status of a host on the backend, independent of the user's enabled/disabled choice */
export type HostConnectionState = "disconnected" | "connecting" | "connected" | "unreachable";
export type HostConnectionStatus = { state: HostConnectionState, error?: string };

export type WithHostConnectionOptions = {
    /** Update the host's connection status from the result (default true). Off for writes, their errors aren't about reachability. */
    track?: boolean
}

type ContainerHostsContextType = {
    hosts: InventoryItem<ContainerHost>[]
    isHostEnabled: (hostName: string) => boolean
    setHostEnabledState: (hostName: string, state: boolean) => void
    getHostStatus: (hostId: string) => HostConnectionStatus
    /** Ask the backend to connect the host. Parallel calls share one request. */
    connectHost: (hostId: string, force?: boolean) => Promise<void>
    /** Connect the host, then run the request. Reconnects once if the backend lost the connection (404). */
    withHostConnection: <T>(hostId: string, request: () => Promise<T>, options?: WithHostConnectionOptions) => Promise<T>
}

// Connections and their status live outside the provider: every page mounts its own provider,
// and the status shouldn't reset (and the sidebar flicker) on navigation.
// One connect request per host; failed attempts are dropped so the next call retries.
const connections: Record<string, Promise<void> | undefined> = {};
let statusSnapshot: Record<string, HostConnectionStatus> = {};
const statusListeners = new Set<() => void>();
const DISCONNECTED: HostConnectionStatus = {state: "disconnected"};

const setStatus = (hostId: string, status: HostConnectionStatus) => {
    const current = statusSnapshot[hostId];
    if (current?.state === status.state && current?.error === status.error) {
        return;
    }
    statusSnapshot = {...statusSnapshot, [hostId]: status};
    statusListeners.forEach((l) => l());
};
const subscribeStatus = (listener: () => void) => {
    statusListeners.add(listener);
    return () => {
        statusListeners.delete(listener);
    };
};
const getStatusSnapshot = () => statusSnapshot;

export const errorMessage = (error: any): string =>
    String(error?.response?.data?.detail ?? error?.message ?? error);

// No response, or the backend couldn't talk to the engine (it answers 400/5xx then).
// 404 means "not connected" and is handled by reconnecting.
const isUnreachableError = (error: any): boolean => {
    if (error?.code === "ERR_CANCELED") return false;
    const status = error?.response?.status;
    return status === undefined || status === 400 || status >= 500;
};

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
    const statuses = React.useSyncExternalStore(subscribeStatus, getStatusSnapshot);

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

    const getHostStatus = React.useCallback(
        (hostId: string): HostConnectionStatus => statuses[hostId] ?? DISCONNECTED,
        [statuses]);

    const connectHost = React.useCallback((hostId: string, force?: boolean): Promise<void> => {
        const existing = connections[hostId];
        if (existing && !force) {
            return existing;
        }
        setStatus(hostId, {state: "connecting"});
        const p: Promise<void> = api.get(`/api/containers/${hostId}/connect`).then(() => {
            setStatus(hostId, {state: "connected"});
        });
        connections[hostId] = p;
        p.catch((error: any) => {
            console.error("Error connecting container host:", hostId, error);
            if (connections[hostId] === p) {
                delete connections[hostId];
                setStatus(hostId, {state: "unreachable", error: errorMessage(error)});
            }
        });
        return p;
    }, [api]);

    const withHostConnection = React.useCallback(async <T, >(
        hostId: string,
        request: () => Promise<T>,
        {track = true}: WithHostConnectionOptions = {},
    ): Promise<T> => {
        const run = async () => {
            try {
                const result = await request();
                if (track) setStatus(hostId, {state: "connected"});
                return result;
            } catch (error) {
                if (track && isUnreachableError(error)) {
                    setStatus(hostId, {state: "unreachable", error: errorMessage(error)});
                }
                throw error;
            }
        };

        await connectHost(hostId);
        try {
            return await run();
        } catch (error: any) {
            // the backend forgets its connections on restart
            if (error?.response?.status !== 404) {
                throw error;
            }
            await connectHost(hostId, true);
            return await run();
        }
    }, [connectHost]);

    const fetchDockerHosts = async (refresh?: boolean) => {
        try {
            const response: InventoryItem<ContainerHost>[] = await api.get("/api/containers/hosts?" + (refresh ? "refresh=true" : ""));
            // sync with the backend: skip the connect request for hosts it has connected already,
            // forget connections it lost (restart)
            response.forEach((h) => {
                if (h.connected && !connections[h.id]) {
                    connections[h.id] = Promise.resolve();
                    setStatus(h.id, {state: "connected"});
                } else if (!h.connected && connections[h.id] && statusSnapshot[h.id]?.state !== "connecting") {
                    delete connections[h.id];
                    setStatus(h.id, DISCONNECTED);
                }
            });
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

    // enabled hosts are kept connected
    React.useEffect(() => {
        hosts.forEach((h) => {
            if (isHostEnabled(h.id) && !connections[h.id]) {
                connectHost(h.id).catch(() => undefined);
            }
        });
    }, [hosts, isHostEnabled, connectHost]);

    console.log("Container Hosts Provider", hosts);

    return (
        <ContainerHostsContext.Provider
            value={{hosts, isHostEnabled, setHostEnabledState, getHostStatus, connectHost, withHostConnection}}>
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
