import {Link} from "react-router";
import {Badge} from "@/components/ui/badge.tsx";
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card.tsx";
import {diskTotal, HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {formatAge, formatBytes} from "@/app/containers/components/stats/format.ts";
import {DiskBar} from "@/app/containers/components/stats/stats-ui.tsx";

const Count = ({value, label}: { value: number, label: string }) => (
    <div>
        <div className="font-semibold tabular-nums">{value}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
    </div>
);

const HostCard = ({stats}: { stats: HostStats }) => {
    const {info, disk, reclaimable, containers, cachedAt} = stats;
    const warnings = info?.Warnings?.length ?? 0;
    return (
        <Card className="gap-4 py-4">
            <CardHeader className="px-4">
                <CardTitle className="flex items-center justify-between gap-2">
                    <Link to={`/containers/${stats.hostId}`} className="truncate hover:underline">{stats.hostId}</Link>
                    {info?.ServerVersion && <Badge variant="outline">Docker {info.ServerVersion}</Badge>}
                </CardTitle>
                <CardDescription className="truncate">
                    {[info?.OperatingSystem, info?.Architecture, info?.KernelVersion].filter(Boolean).join(" · ") || "No engine info cached"}
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 px-4 text-sm">
                <div className="grid grid-cols-4 gap-2 text-center">
                    <Count value={containers.running} label="running" />
                    <Count value={containers.paused} label="paused" />
                    <Count value={containers.stopped} label="stopped" />
                    <Count value={stats.imageCount} label="images" />
                </div>

                {info && (
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        {info.NCPU !== undefined && <span>{info.NCPU} CPUs</span>}
                        {info.MemTotal !== undefined && <span>{formatBytes(info.MemTotal)} RAM</span>}
                        {info.Driver && <span>{info.Driver}</span>}
                        {info.Swarm?.LocalNodeState && info.Swarm.LocalNodeState !== "inactive" && <span>swarm: {info.Swarm.LocalNodeState}</span>}
                        {warnings > 0 && <span className="text-amber-600" title={info.Warnings?.join("\n")}>{warnings} warning{warnings > 1 ? "s" : ""}</span>}
                    </div>
                )}

                {disk ? (
                    <div className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                            <span>Disk {formatBytes(diskTotal(disk))}</span>
                            <span className="text-muted-foreground">{formatBytes(diskTotal(reclaimable))} reclaimable</span>
                        </div>
                        <DiskBar disk={disk} />
                    </div>
                ) : (
                    <div className="text-xs text-muted-foreground">No disk usage cached</div>
                )}

                {stats.topImages.length > 0 && (
                    <div className="space-y-1">
                        <div className="text-xs font-medium">Largest images</div>
                        {stats.topImages.map((img) => (
                            <div key={img.name} className="flex justify-between gap-2 text-xs">
                                <span className="truncate font-mono" title={img.name}>{img.name}</span>
                                <span className="shrink-0 tabular-nums text-muted-foreground">{formatBytes(img.size)}</span>
                            </div>
                        ))}
                    </div>
                )}

                <div className="text-xs text-muted-foreground">
                    Cached: info {formatAge(cachedAt.info)} · df {formatAge(cachedAt.df)} · containers {formatAge(cachedAt.containers)}
                </div>
            </CardContent>
        </Card>
    );
};

export default HostCard;
