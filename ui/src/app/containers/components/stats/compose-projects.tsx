import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {
    composeProjects,
    hostsWithContainerList,
    unmanagedContainerCount,
} from "@/app/containers/components/stats/insights.ts";
import {
    CoverageNote,
    EmptyNote,
    HostLink,
    StatsSection,
    useRowLimit,
} from "@/app/containers/components/stats/stats-ui.tsx";

const ComposeProjects = ({stats}: { stats: HostStats[] }) => {
    const projects = composeProjects(stats);
    const {visible, toggle} = useRowLimit(projects, 15);
    const degraded = projects.filter((p) => p.running > 0 && p.running < p.total).length;
    const down = projects.filter((p) => p.running === 0).length;

    return (
        <StatsSection
            title="Compose projects"
            description={`${projects.length} projects · ${unmanagedContainerCount(stats)} containers not managed by compose`}
            action={<div className="flex gap-1">
                {degraded > 0 && <Badge variant="secondary">{degraded} partly up</Badge>}
                {down > 0 && <Badge variant="outline">{down} down</Badge>}
            </div>}
        >
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {projects.length === 0 ? <EmptyNote>No compose projects found.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Project</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Services</TableHead>
                                <TableHead>Working dir</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((p) => {
                                const status = p.running === p.total ? "up" : p.running === 0 ? "down" : "partly up";
                                return (
                                    <TableRow key={`${p.hostId}-${p.project}`}>
                                        <TableCell className="font-medium">{p.project}</TableCell>
                                        <TableCell><HostLink hostId={p.hostId} /></TableCell>
                                        <TableCell>
                                            <Badge variant={status === "up" ? "default" : status === "down" ? "outline" : "secondary"}>
                                                {p.running}/{p.total} {status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="max-w-[260px] truncate text-xs" title={p.services.join(", ")}>
                                            {p.services.join(", ")}
                                        </TableCell>
                                        <TableCell className="max-w-[220px] truncate font-mono text-xs text-muted-foreground" title={p.workingDir}>
                                            {p.workingDir}
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

export default ComposeProjects;
