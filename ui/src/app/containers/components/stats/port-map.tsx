import {Badge} from "@/components/ui/badge.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {hostsWithContainerList, portRows} from "@/app/containers/components/stats/insights.ts";
import {
    CoverageNote,
    EmptyNote,
    HostLink,
    StatsSection,
    useRowLimit,
} from "@/app/containers/components/stats/stats-ui.tsx";

const PortMap = ({stats}: { stats: HostStats[] }) => {
    const rows = portRows(stats);
    const {visible, toggle} = useRowLimit(rows, 20);
    const conflicts = rows.filter((r) => r.conflict).length;
    const exposed = rows.filter((r) => r.public && r.running).length;

    return (
        <StatsSection
            title="Published ports"
            description="Host port bindings of all containers, including stopped ones"
            action={<div className="flex gap-1">
                {conflicts > 0 && <Badge variant="destructive">{conflicts} conflicts</Badge>}
                <Badge variant="outline">{exposed} on all interfaces</Badge>
            </div>}
        >
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {rows.length === 0 ? <EmptyNote>No published ports.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Host</TableHead>
                                <TableHead>Host port</TableHead>
                                <TableHead>Bind address</TableHead>
                                <TableHead>Container</TableHead>
                                <TableHead>Container port</TableHead>
                                <TableHead />
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r, i) => (
                                <TableRow key={i} className={r.running ? "" : "text-muted-foreground"}>
                                    <TableCell><HostLink hostId={r.hostId} /></TableCell>
                                    <TableCell className="font-mono tabular-nums">{r.hostPort}</TableCell>
                                    <TableCell className="font-mono text-xs">{r.hostIp}</TableCell>
                                    <TableCell className="font-mono text-xs">{r.container}{!r.running && " (stopped)"}</TableCell>
                                    <TableCell className="font-mono text-xs">{r.containerPort}</TableCell>
                                    <TableCell className="space-x-1 text-right">
                                        {r.conflict && <Badge variant="destructive">conflict</Badge>}
                                        {r.public && <Badge variant="outline">public</Badge>}
                                    </TableCell>
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

export default PortMap;
