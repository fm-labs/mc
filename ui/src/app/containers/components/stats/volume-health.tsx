import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {volumeRows} from "@/app/containers/components/stats/insights.ts";
import {EmptyNote, HostLink, StatsSection, useRowLimit} from "@/app/containers/components/stats/stats-ui.tsx";

const VolumeHealth = ({stats}: { stats: HostStats[] }) => {
    const rows = volumeRows(stats);
    const orphans = rows.filter((r) => r.refCount === 0);
    const {visible, toggle} = useRowLimit(rows, 10);

    return (
        <StatsSection
            title="Volumes"
            description="Largest volumes first, with the containers that mount them"
            action={orphans.length > 0 && (
                <Badge variant="secondary">
                    {orphans.length} unused · {formatBytes(orphans.reduce((a, r) => a + r.size, 0))}
                </Badge>
            )}
        >
            {rows.length === 0 ? <EmptyNote>No volumes cached</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Volume</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead>Used by</TableHead>
                                <TableHead className="text-right">Size</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r) => (
                                <TableRow key={`${r.hostId}-${r.name}`}>
                                    <TableCell className="max-w-[240px] truncate font-mono text-xs" title={r.name}>{r.name}</TableCell>
                                    <TableCell><HostLink hostId={r.hostId} path="/volumes" /></TableCell>
                                    <TableCell className="max-w-[260px] truncate text-xs">
                                        {r.refCount === 0
                                            ? <Badge variant="outline">unused</Badge>
                                            : r.usedBy.join(", ") || <span className="text-muted-foreground">{r.refCount} container{r.refCount > 1 ? "s" : ""}</span>}
                                    </TableCell>
                                    <TableCell className="text-right tabular-nums">{formatBytes(r.size)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {toggle}
                </>
            )}
        </StatsSection>
    );
};

export default VolumeHealth;
