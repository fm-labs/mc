import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {warningRows} from "@/app/containers/components/stats/insights.ts";
import {EmptyNote, HostLink, StatsSection} from "@/app/containers/components/stats/stats-ui.tsx";

const WarningsPanel = ({stats}: { stats: HostStats[] }) => {
    const rows = warningRows(stats);
    return (
        <StatsSection title="Engine warnings" description="Reported by docker info on each host">
            {rows.length === 0 ? <EmptyNote>No engine warnings.</EmptyNote> : (
                <ul className="space-y-2 text-sm">
                    {rows.map((r, i) => (
                        <li key={i} className="flex gap-3">
                            <span className="w-32 shrink-0 truncate font-medium"><HostLink hostId={r.hostId} /></span>
                            <span className="text-amber-600">{r.warning}</span>
                        </li>
                    ))}
                </ul>
            )}
        </StatsSection>
    );
};

export default WarningsPanel;
