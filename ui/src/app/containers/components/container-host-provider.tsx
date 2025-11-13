import React from "react";
import {useApi} from "@/context/api-context.tsx";
import {cached} from "@/utils/session-cache.ts";

type ContainerHostContextConfig = {
    hostId: string,
}

type ContainerHostContextType = {
    config: ContainerHostContextConfig
    info?: any,
    summary?: any,
    containers?: Record<string, any>,
    //images?: Record<string, any>,
    fetchContainerData: (path: string) => Promise<any>,
    fetchInfo: (force?: boolean) => Promise<any>,
    fetchSummary: (force?: boolean) => Promise<any>,
    fetchContainers: (force?: boolean) => Promise<any>,
    fetchImages: (force?: boolean) => Promise<any>,
    fetchVolumes: (force?: boolean) => Promise<any>,
    autorefreshInterval: number,
    setAutoRefreshInterval: (interval: number) => void,
    error?: string | null,
}

export const ContainerHostContext = React.createContext<ContainerHostContextType | undefined>(undefined);


export const ContainerHostProvider: React.FC<{ children: React.ReactNode, config: any }> = ({ children, config }) => {
    const { api } = useApi()

    const [error, setError] = React.useState<string | null>(null);
    const [info, setInfo] = React.useState<any>(null);
    const [summary, setSummary] = React.useState<any>(null);
    const [containers, setContainers] = React.useState<Record<string, any>>([]);
    //const [images, setImages] = React.useState<Record<string, any>>([]);
    const [autorefreshInterval, setAutoRefreshInterval] = React.useState<number>(30000);


    const _fetchContainerData = React.useCallback(async (path: string) => {
        try {
            if (!config || config.hostId === undefined || config.hostId === null) {
                //throw new Error("No hostId configured");
                setError("No hostId configured");
                return;
            }
            const hostId = config.hostId;
            const response = await api.get(`/api/containers/${hostId}/${path}`);
            //console.log("Data fetched:", path, response);
            setError(null);
            return response;
        } catch (error) {
            console.error("Error fetching container data:", path, error);
            //toast.error("Error fetching container data " + path);
            setError("Error fetching container data: " + String(error));
        }
    }, [config, setError, api])

    const fetchContainerData = React.useCallback((path: string, force?: boolean, ttl?: number) => {
        const cacheKey = `container_host_${config.hostId}_path_${path}`;
        const p = () => _fetchContainerData(path)
        return cached(cacheKey, p, ttl || autorefreshInterval - 1, force); // make sure cache TTL is less than autorefresh interval
    }, [config.hostId, _fetchContainerData, autorefreshInterval]);

    const fetchInfo = React.useCallback(async (force?: boolean) => {
        const response = await fetchContainerData("info", force);
        //console.log("Info Data fetched:", response);
        setInfo(response);
        return response;
    }, [fetchContainerData, setInfo])

    const fetchSummary = React.useCallback(async (force?: boolean) => {
        const response = await fetchContainerData("df", force);
        //console.log("Summary Data fetched:", response);
        setSummary(response);
        return response;
    }, [fetchContainerData, setSummary])

    const fetchContainers = React.useCallback(async (force?: boolean) => {
        const response = await fetchContainerData("containers", force);
        //console.log("Containers Data fetched:", response);
        setContainers(response);
        return response;
    }, [fetchContainerData, setContainers])

    const fetchImages = React.useCallback(async (force?: boolean) => {
        return await fetchContainerData("images", force, 120000);
    }, [fetchContainerData])

    const fetchVolumes = React.useCallback(async (force?: boolean) => {
        return await fetchContainerData("volumes", force, 120000);
    }, [fetchContainerData])

    // const updateAll = React.useCallback(async (force?: boolean) => {
    //     await Promise.all([
    //         //fetchInfo(),
    //         fetchSummary(),
    //         fetchContainers(force),
    //         //fetchImages()
    //     ]);
    // }, [fetchContainers, fetchSummary])

    React.useEffect(() => {
        if (!config || config.hostId === undefined || config.hostId === null) {
            return;
        }

        // Initial fetch
        console.log("Initial fetch for Container host", config.hostId, autorefreshInterval);
        fetchInfo().then(fetchContainers).then(fetchSummary).catch(() => {
            console.warn("Error fetching initial container data");
        })

        // Auto-refresh
        let containerUpdateTimer: any;
        let summeryUpdateTimer: any;
        if (autorefreshInterval && autorefreshInterval > 0) {
            console.log("Container AutorefreshInterval:", autorefreshInterval);
            // modifying the interval withing a range to avoid too much parallel requests
            // if many hosts are monitored at the same time
            const min_interval = Math.max(5000, autorefreshInterval - 2000);
            const max_interval = autorefreshInterval + 2000;
            const _interval = Math.floor(Math.random() * (max_interval - min_interval + 1)) + min_interval;
            console.log("Container AutorefreshInterval (with jitter):", _interval);
            containerUpdateTimer = setInterval(fetchContainers, _interval);
            summeryUpdateTimer = setInterval(fetchSummary, _interval * 2.5); // update less frequent
        }

        return () => {
            if (containerUpdateTimer) {
                clearInterval(containerUpdateTimer);
            }
            if (summeryUpdateTimer) {
                clearInterval(summeryUpdateTimer);
            }
        }
    }, [config.hostId, autorefreshInterval]);

    return (
        <ContainerHostContext.Provider value={{
            config,
            info,
            summary,
            containers,
            fetchContainerData,
            fetchInfo,
            fetchSummary,
            fetchContainers,
            fetchImages,
            fetchVolumes,
            autorefreshInterval,
            setAutoRefreshInterval,
            error
        }}>
            {children}
        </ContainerHostContext.Provider>
    );
}

//@es-lint-disable-next-line react-refresh/only-export-components
export const useContainerHost = () => {
    const context = React.useContext(ContainerHostContext);
    if (context === undefined) {
        throw new Error("useContainerHost must be used within a ContainerHostProvider");
    }
    return context;
}
