import { useHost } from "@/app/infrastructure/host/host-provider.tsx";
import { formatDistanceToNow } from "date-fns";

export const HostStatus = ({ showText }: { showText?: boolean }) => {
    const { host } = useHost()
    const _status = host?.ping?.result?.status || "unknown";
    const _lastChecked = host?.ping?.timestamp || 0;
    const _timeAgo = _lastChecked > 0
        ? formatDistanceToNow(new Date(_lastChecked * 1000), {addSuffix: true})
        : "unknown"

    let colorClass = "bg-gray-500";
    if (_status==="reachable") {
        colorClass = "bg-green-500";
    } else if (_status==="unreachable") {
        colorClass = "bg-red-500";
    } else if (_status==="unknown") {
        colorClass = "bg-gray-500";
    }

    return (
        <span>
            <span className={`inline-block ml-1 w-3 h-3 rounded-full ${colorClass}`}
                  title={`${_status} - Last checked: ${_timeAgo}`}></span>
            {showText && ` ${_status}`}
        </span>
    );
};
