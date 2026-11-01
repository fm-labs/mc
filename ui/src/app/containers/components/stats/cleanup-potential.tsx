import {Bar, BarChart, CartesianGrid, XAxis, YAxis} from "recharts";
import {
    ChartContainer,
    ChartLegend,
    ChartLegendContent,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {CountSize, diskTotal, HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {
    barHeight,
    diskConfig,
    diskKeys,
    EmptyNote,
    HostLink,
    StatsSection,
    tooltipRow,
} from "@/app/containers/components/stats/stats-ui.tsx";

const Cell2 = ({cs}: { cs: CountSize }) => (
    <TableCell className="text-right tabular-nums">
        {cs.count > 0 ? <>{cs.count} <span className="text-muted-foreground">· {formatBytes(cs.size)}</span></> : <span className="text-muted-foreground">—</span>}
    </TableCell>
);

// What `docker system prune -a --volumes` would free, per host, biggest first
const CleanupPotential = ({stats}: { stats: HostStats[] }) => {
    const hosts = stats
        .filter((s) => s.reclaimable && s.cleanup)
        .sort((a, b) => diskTotal(b.reclaimable) - diskTotal(a.reclaimable));
    const data = hosts.filter((s) => diskTotal(s.reclaimable) > 0).map((s) => ({host: s.hostId, ...s.reclaimable}));

    return (
        <StatsSection title="Cleanup potential"
                      description="Space freed by removing unused images, stopped containers, unused volumes and build cache">
            {hosts.length === 0 ? <EmptyNote>No disk usage cached</EmptyNote> : (
                <div className="space-y-6">
                    {data.length > 0 ? (
                        <ChartContainer config={diskConfig} className="aspect-auto w-full" style={barHeight(data.length)}>
                            <BarChart data={data} layout="vertical" margin={{left: 8, right: 8}}>
                                <CartesianGrid horizontal={false} />
                                <XAxis type="number" tickFormatter={(v) => formatBytes(v, 0)} tickLine={false} axisLine={false} />
                                <YAxis type="category" dataKey="host" width={110} tickLine={false} axisLine={false} />
                                <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(diskConfig, formatBytes)} />} />
                                <ChartLegend content={<ChartLegendContent />} />
                                {diskKeys.map((k, i) => (
                                    <Bar key={k} dataKey={k} stackId="reclaim" fill={`var(--color-${k})`}
                                         radius={i === diskKeys.length - 1 ? [0, 4, 4, 0] : 0} />
                                ))}
                            </BarChart>
                        </ChartContainer>
                    ) : <EmptyNote>Nothing to clean up.</EmptyNote>}

                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Host</TableHead>
                                <TableHead className="text-right">Reclaimable</TableHead>
                                <TableHead className="text-right">Dangling images</TableHead>
                                <TableHead className="text-right">Unused images</TableHead>
                                <TableHead className="text-right">Stopped containers</TableHead>
                                <TableHead className="text-right">Unused volumes</TableHead>
                                <TableHead className="text-right">Build cache</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {hosts.map((s) => (
                                <TableRow key={s.hostId}>
                                    <TableCell className="font-medium"><HostLink hostId={s.hostId} /></TableCell>
                                    <TableCell className="text-right font-medium tabular-nums">{formatBytes(diskTotal(s.reclaimable))}</TableCell>
                                    <Cell2 cs={s.cleanup!.danglingImages} />
                                    <Cell2 cs={s.cleanup!.unusedImages} />
                                    <Cell2 cs={s.cleanup!.stoppedContainers} />
                                    <Cell2 cs={s.cleanup!.orphanVolumes} />
                                    <Cell2 cs={s.cleanup!.buildCache} />
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}
        </StatsSection>
    );
};

export default CleanupPotential;
