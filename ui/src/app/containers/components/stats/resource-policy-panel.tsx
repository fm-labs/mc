import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {hostsWithContainerList, policyRows} from "@/app/containers/components/stats/insights.ts";
import {
    ContainerLink,
    CoverageNote,
    EmptyNote,
    HostLink,
    StatsSection,
    useRowLimit,
} from "@/app/containers/components/stats/stats-ui.tsx";

const ResourcePolicyPanel = ({stats}: { stats: HostStats[] }) => {
    const rows = policyRows(stats);
    const {visible, toggle} = useRowLimit(rows, 10);
    const noLimits = rows.filter((r) => r.noLimits).length;
    const noRestart = rows.filter((r) => r.noRestart).length;

    return (
        <StatsSection
            title="Limits and restart policy"
            description="Containers without CPU/memory limits or without a restart policy"
            action={<div className="flex gap-1">
                <Badge variant="outline">{noLimits} no limits</Badge>
                <Badge variant="outline">{noRestart} no restart</Badge>
            </div>}
        >
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {rows.length === 0 ? <EmptyNote>All containers have limits and a restart policy.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Container</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead>State</TableHead>
                                <TableHead>No limits</TableHead>
                                <TableHead>No restart policy</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r) => (
                                <TableRow key={`${r.hostId}-${r.containerId}`}>
                                    <TableCell><ContainerLink hostId={r.hostId} containerId={r.containerId} name={r.name} /></TableCell>
                                    <TableCell><HostLink hostId={r.hostId} /></TableCell>
                                    <TableCell className="text-muted-foreground">{r.running ? "running" : "stopped"}</TableCell>
                                    <TableCell>{r.noLimits ? "✕" : ""}</TableCell>
                                    <TableCell>{r.noRestart ? "✕" : ""}</TableCell>
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

export default ResourcePolicyPanel;
