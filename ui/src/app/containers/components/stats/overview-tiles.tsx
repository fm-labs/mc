import {diskTotal, HostStats, sumDisk} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {StatTile} from "@/app/containers/components/stats/stats-ui.tsx";
import {attentionItems} from "@/app/containers/components/stats/insights.ts";

const OverviewTiles = ({stats, hostCount}: { stats: HostStats[], hostCount: number }) => {
    const total = (fn: (s: HostStats) => number) => stats.reduce((a, s) => a + fn(s), 0);
    const disk = sumDisk(stats.map((s) => s.disk));
    const reclaimable = sumDisk(stats.map((s) => s.reclaimable));
    const attention = attentionItems(stats).length;

    return (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-7">
            <StatTile icon="container-host" label="Hosts" value={`${stats.length}/${hostCount}`} sub="with cached data" />
            <StatTile icon="container" label="Containers" value={total((s) => s.containers.total)}
                      sub={`${total((s) => s.containers.running)} running`} />
            <StatTile icon="container-image" label="Images" value={total((s) => s.imageCount)} />
            <StatTile icon="container-volume" label="Volumes" value={total((s) => s.volumeCount)} />
            <StatTile icon="host" label="Capacity" value={`${total((s) => s.info?.NCPU ?? 0)} CPUs`}
                      sub={`${formatBytes(total((s) => s.info?.MemTotal ?? 0))} RAM`} />
            <StatTile icon="database" label="Disk used" value={formatBytes(diskTotal(disk))}
                      sub={`${formatBytes(diskTotal(reclaimable))} reclaimable`} />
            <StatTile icon="warning" label="Need attention" value={attention} tone={attention ? "warn" : undefined}
                      sub="containers" />
        </div>
    );
};

export default OverviewTiles;
