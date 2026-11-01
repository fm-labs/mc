import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {driftFields, majorityValues} from "@/app/containers/components/stats/insights.ts";
import {EmptyNote, HostLink, StatsSection} from "@/app/containers/components/stats/stats-ui.tsx";

// Engine versions per host; values that differ from the most common one are highlighted
const VersionDrift = ({stats}: { stats: HostStats[] }) => {
    const hosts = stats.filter((s) => s.info);
    const majority = majorityValues(hosts);
    const drifting = hosts.filter((s) => driftFields.some(({key}) =>
        majority[key] !== undefined && s.info?.[key] !== undefined && String(s.info[key]) !== majority[key])).length;

    return (
        <StatsSection title="Version drift"
                      description={drifting ? `${drifting} host${drifting > 1 ? "s" : ""} differ from the most common setup (highlighted)` : "All hosts match"}>
            {hosts.length === 0 ? <EmptyNote>No engine info cached</EmptyNote> : (
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Host</TableHead>
                            {driftFields.map((f) => <TableHead key={f.key}>{f.label}</TableHead>)}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {hosts.map((s) => (
                            <TableRow key={s.hostId}>
                                <TableCell className="font-medium"><HostLink hostId={s.hostId} /></TableCell>
                                {driftFields.map(({key}) => {
                                    const v = s.info?.[key];
                                    const differs = majority[key] !== undefined && v !== undefined && String(v) !== majority[key];
                                    return (
                                        <TableCell key={key}
                                                   className={`max-w-[200px] truncate text-xs ${differs ? "font-medium text-amber-600" : "text-muted-foreground"}`}
                                                   title={differs ? `most hosts: ${majority[key]}` : undefined}>
                                            {v !== undefined ? String(v) : "—"}
                                        </TableCell>
                                    );
                                })}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}
        </StatsSection>
    );
};

export default VersionDrift;
