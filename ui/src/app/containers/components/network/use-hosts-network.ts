import React from "react";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import {useApi} from "@/context/api-context.tsx";
import {cached, readCached} from "@/utils/session-cache.ts";
import {
    HostNetworkData,
    hostCacheKey,
    NETWORK_PATHS,
    readHostNetworkData,
} from "@/app/containers/components/network/network-graph.ts";

// Re-read the session cache this often (local only, no API calls)
const RELOAD_INTERVAL = 10000;

export type FetchResult = { ok: string[], failed: { hostId: string, error: string }[] };

// Network data of all enabled hosts, read from the browser session cache.
// Only paths missing from the cache are fetched; `refresh` force-fetches everything.
export const useHostsNetwork = () => {
    const {hosts, isHostEnabled} = useContainerHosts();
    const {api} = useApi();
    const [tick, setTick] = React.useState(0);
    const [fetching, setFetching] = React.useState(false);

    // the host provider caches by host name, the routes use the id
    const hostIds = React.useMemo(
        () => hosts.map((h) => h.name ?? h.id).filter((id) => isHostEnabled(id)),
        [hosts, isHostEnabled]);

    React.useEffect(() => {
        const timer = setInterval(() => setTick((t) => t + 1), RELOAD_INTERVAL);
        return () => clearInterval(timer);
    }, []);

    const load = React.useCallback(async (force: boolean): Promise<FetchResult> => {
        const jobs = hostIds.map((hostId) => {
            const paths = force ? NETWORK_PATHS : NETWORK_PATHS.filter((p) => !readCached(hostCacheKey(hostId, p))?.data);
            return Promise.all(paths.map((path) =>
                cached(hostCacheKey(hostId, path), () => api.get(`/api/containers/${hostId}/${path}`), 0, force)));
        });
        if (jobs.length === 0) return {ok: [], failed: []};
        setFetching(true);
        try {
            const results = await Promise.allSettled(jobs);
            return {
                ok: hostIds.filter((_, i) => results[i].status === "fulfilled"),
                failed: hostIds
                    .map((hostId, i) => ({hostId, r: results[i]}))
                    .filter(({r}) => r.status === "rejected")
                    .map(({hostId, r}) => {
                        const reason = (r as PromiseRejectedResult).reason;
                        return {hostId, error: String(reason?.message ?? reason)};
                    }),
            };
        } finally {
            setFetching(false);
            setTick((t) => t + 1);
        }
    }, [hostIds, api]);

    // fill gaps in the cache once per set of enabled hosts
    React.useEffect(() => {
        load(false).catch(() => undefined);
    }, [load]);

    const refresh = React.useCallback(() => load(true), [load]);

    const {data, missing} = React.useMemo(() => {
        const data: HostNetworkData[] = [];
        const missing: string[] = [];
        hostIds.forEach((hostId) => {
            const d = readHostNetworkData(hostId);
            if (d) data.push(d); else missing.push(hostId);
        });
        return {data, missing};
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hostIds, tick]);

    return {hosts, hostIds, data, missing, fetching, refresh};
};
