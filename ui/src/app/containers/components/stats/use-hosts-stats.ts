import React from "react";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import {HostStats, readHostStats} from "@/app/containers/components/stats/host-stats.ts";

// Re-read the session cache this often (local only, no API calls)
const RELOAD_INTERVAL = 10000;

export const useHostsStats = () => {
    const {hosts} = useContainerHosts();
    const [tick, setTick] = React.useState(0);

    React.useEffect(() => {
        const timer = setInterval(() => setTick((t) => t + 1), RELOAD_INTERVAL);
        return () => clearInterval(timer);
    }, []);

    const reload = React.useCallback(() => setTick((t) => t + 1), []);

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

    return {hosts, stats, missing, reload};
};
