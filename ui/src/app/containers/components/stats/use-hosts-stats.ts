import React from "react";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import {HostStats, readHostStats} from "@/app/containers/components/stats/host-stats.ts";
import {useApi} from "@/context/api-context.tsx";
import {cached} from "@/utils/session-cache.ts";

// paths re-fetched by fetchAll; the cache keys match ContainerHostProvider.fetchContainerData
const FETCH_PATHS = ["info", "df"];

export type FetchAllResult = { ok: string[], failed: { hostId: string, error: string }[] };

// Re-read the session cache this often (local only, no API calls)
const RELOAD_INTERVAL = 10000;

export const useHostsStats = () => {
    const {hosts, isHostEnabled, withHostConnection} = useContainerHosts();
    const {api} = useApi();
    const [tick, setTick] = React.useState(0);
    const [fetching, setFetching] = React.useState(false);

    React.useEffect(() => {
        const timer = setInterval(() => setTick((t) => t + 1), RELOAD_INTERVAL);
        return () => clearInterval(timer);
    }, []);

    const reload = React.useCallback(() => setTick((t) => t + 1), []);

    // Force-fetch info and df of all connected hosts into the session cache
    const fetchAll = React.useCallback(async (): Promise<FetchAllResult> => {
        const hostIds = hosts.map((h) => h.name ?? h.id).filter((id) => isHostEnabled(id));
        setFetching(true);
        try {
            const results = await Promise.allSettled(hostIds.map((hostId) =>
                Promise.all(FETCH_PATHS.map((path) =>
                    cached(`container_host_${hostId}_path_${path}`,
                        () => withHostConnection(hostId, () => api.get(`/api/containers/${hostId}/${path}`)), 0, true)))));
            return {
                ok: hostIds.filter((_, i) => results[i].status === "fulfilled"),
                failed: hostIds
                    .map((hostId, i) => ({hostId, r: results[i]}))
                    .filter(({r}) => r.status === "rejected")
                    .map(({hostId, r}) => ({hostId, error: String((r as PromiseRejectedResult).reason?.message ?? (r as PromiseRejectedResult).reason)})),
            };
        } finally {
            setFetching(false);
            setTick((t) => t + 1);
        }
    }, [hosts, isHostEnabled, api, withHostConnection]);

    const {stats, missing} = React.useMemo(() => {
        const stats: HostStats[] = [];
        const missing: string[] = [];
        hosts.forEach((h) => {
            // the host provider caches by host name, the routes use the id
            const hostId = h.name ?? h.id;
            const s = readHostStats(hostId);
            if (s) stats.push(s); else missing.push(hostId);
        });
        return {stats, missing};
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hosts, tick]);

    return {hosts, stats, missing, reload, fetchAll, fetching};
};
