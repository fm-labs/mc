import {useMemo} from "react";
import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {VolumeRow, volumeRows} from "@/app/containers/components/stats/insights.ts";
import {
    diskConfig,
    EmptyNote,
    HostLink,
    SortableHead,
    StatsSection,
    useRowLimit,
    useSort,
} from "@/app/containers/components/stats/stats-ui.tsx";

// Same colors as the "In use / Unused" image charts
const IN_USE = "var(--chart-2)";
const UNUSED = "var(--chart-1)";

const sortColumns = {
    name: (r: VolumeRow) => r.name,
    host: (r: VolumeRow) => r.hostId,
    usedBy: (r: VolumeRow) => r.refCount,
    size: (r: VolumeRow) => r.size,
};

const Dot = ({color}: { color: string }) => (
    <span className="inline-block size-2 shrink-0 rounded-full" style={{backgroundColor: color}} />
);

const VolumeHealth = ({stats}: { stats: HostStats[] }) => {
    const rows = useMemo(() => volumeRows(stats), [stats]);
    const orphans = rows.filter((r) => r.refCount === 0);
    const maxSize = Math.max(0, ...rows.map((r) => r.size));
    const {sorted, sort, toggleSort} = useSort(rows, sortColumns, {key: "size", dir: "desc"});
    const {visible, toggle} = useRowLimit(sorted, 10);

    return (
        <StatsSection
            title="Volumes"
            description={
                <span className="inline-flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span>Volumes and the containers that mount them</span>
                    <span className="inline-flex items-center gap-1.5"><Dot color={IN_USE} /> in use</span>
                    <span className="inline-flex items-center gap-1.5"><Dot color={UNUSED} /> unused</span>
                </span>
            }
            action={orphans.length > 0 && (
                <Badge variant="outline" style={{borderColor: UNUSED, color: UNUSED}}>
                    {orphans.length} unused · {formatBytes(orphans.reduce((a, r) => a + r.size, 0))}
                </Badge>
            )}
        >
            {rows.length === 0 ? <EmptyNote>No volumes cached</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <SortableHead column="name" sort={sort} onSort={toggleSort}>Volume</SortableHead>
                                <SortableHead column="host" sort={sort} onSort={toggleSort}>Host</SortableHead>
                                <SortableHead column="usedBy" sort={sort} onSort={toggleSort}>Used by</SortableHead>
                                <SortableHead column="size" sort={sort} onSort={toggleSort} className="text-right">Size</SortableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r) => {
                                const unused = r.refCount === 0;
                                return (
                                    <TableRow key={`${r.hostId}-${r.name}`}>
                                        <TableCell className="max-w-[240px] font-mono text-xs" title={r.name}>
                                            <span className="flex items-center gap-2">
                                                <Dot color={unused ? UNUSED : IN_USE} />
                                                <span className="truncate">{r.name}</span>
                                            </span>
                                        </TableCell>
                                        <TableCell><HostLink hostId={r.hostId} path="/volumes" /></TableCell>
                                        <TableCell className="max-w-[260px] truncate text-xs">
                                            {unused
                                                ? <Badge variant="outline" style={{borderColor: UNUSED, color: UNUSED}}>unused</Badge>
                                                : r.usedBy.join(", ") || <span className="text-muted-foreground">{r.refCount} container{r.refCount > 1 ? "s" : ""}</span>}
                                        </TableCell>
                                        <TableCell className="text-right tabular-nums">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="hidden h-1.5 w-20 overflow-hidden rounded-full bg-muted sm:block">
                                                    <div className="h-full rounded-full"
                                                         style={{
                                                             width: `${maxSize ? (r.size / maxSize) * 100 : 0}%`,
                                                             backgroundColor: unused ? UNUSED : diskConfig.volumes.color,
                                                         }} />
                                                </div>
                                                <span className="min-w-16">{formatBytes(r.size)}</span>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                    {toggle}
                </>
            )}
        </StatsSection>
    );
};

export default VolumeHealth;
