import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {
    AttentionKind,
    attentionItems,
    hostsWithContainerList,
    LONG_STOPPED_DAYS,
} from "@/app/containers/components/stats/insights.ts";
import {
    ContainerLink,
    CoverageNote,
    EmptyNote,
    HostLink,
    StatsSection,
    useRowLimit,
} from "@/app/containers/components/stats/stats-ui.tsx";

const kindLabel: Record<AttentionKind, { label: string, variant: "destructive" | "secondary" | "outline" }> = {
    "unhealthy": {label: "Unhealthy", variant: "destructive"},
    "oom": {label: "OOM killed", variant: "destructive"},
    "restarting": {label: "Restarts", variant: "secondary"},
    "exited": {label: "Exit error", variant: "secondary"},
    "long-stopped": {label: "Long stopped", variant: "outline"},
};

const AttentionPanel = ({stats}: { stats: HostStats[] }) => {
    const items = attentionItems(stats);
    const {visible, toggle} = useRowLimit(items, 15);
    const counts = items.reduce<Partial<Record<AttentionKind, number>>>((acc, i) => ({...acc, [i.kind]: (acc[i.kind] ?? 0) + 1}), {});

    return (
        <StatsSection
            title="Needs attention"
            description={`Unhealthy, OOM killed, restarting, failed, or stopped for more than ${LONG_STOPPED_DAYS} days`}
            action={<div className="flex flex-wrap justify-end gap-1">
                {(Object.keys(kindLabel) as AttentionKind[]).filter((k) => counts[k]).map((k) => (
                    <Badge key={k} variant={kindLabel[k].variant}>{kindLabel[k].label}: {counts[k]}</Badge>
                ))}
            </div>}
        >
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {items.length === 0 ? <EmptyNote>All containers look fine.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Issue</TableHead>
                                <TableHead>Container</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead>Image</TableHead>
                                <TableHead>Details</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((i) => (
                                <TableRow key={`${i.hostId}-${i.containerId}-${i.kind}`}>
                                    <TableCell><Badge variant={kindLabel[i.kind].variant}>{kindLabel[i.kind].label}</Badge></TableCell>
                                    <TableCell><ContainerLink hostId={i.hostId} containerId={i.containerId} name={i.name} /></TableCell>
                                    <TableCell><HostLink hostId={i.hostId} /></TableCell>
                                    <TableCell className="max-w-[240px] truncate font-mono text-xs" title={i.image}>{i.image}</TableCell>
                                    <TableCell className="text-muted-foreground">{i.detail}</TableCell>
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

export default AttentionPanel;
