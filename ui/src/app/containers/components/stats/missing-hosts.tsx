import {Link} from "react-router";
import {Badge} from "@/components/ui/badge.tsx";
import {StatsSection} from "@/app/containers/components/stats/stats-ui.tsx";
import {HostStatusDot} from "@/app/containers/components/host-status.tsx";

const MissingHosts = ({hostIds}: { hostIds: string[] }) => {
    if (hostIds.length === 0) return null;
    return (
        <StatsSection title="No cached data" description="These hosts have not been loaded in this browser session yet.">
            <div className="flex flex-wrap gap-2">
                {hostIds.map((id) => (
                    <Link key={id} to={`/containers/${id}`}>
                        <Badge variant="secondary"><HostStatusDot hostId={id}/>{id}</Badge>
                    </Link>
                ))}
            </div>
        </StatsSection>
    );
};

export default MissingHosts;
