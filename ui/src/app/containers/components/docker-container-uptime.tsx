import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { formatDistanceToNow}  from "date-fns";
import { SignalZero, SignalLow, SignalMedium, SignalHigh } from "lucide-react";


const signalMap = {
    zero: {
        icon: SignalZero,
        color: "red",
        minimumUptimeMs: 0,
    },
    low: {
        icon: SignalLow,
        color: "rgb(218,121,8)",
        minimumUptimeMs: 15 * 60 * 1000, // 15 minutes
    },
    medium: {
        icon: SignalMedium,
        color: "rgb(145,225,56)",
        minimumUptimeMs: 120 * 60 * 1000, // 120 minutes
    },
    high: {
        icon: SignalHigh,
        color: "green",
        minimumUptimeMs: Infinity,
    }
}


const DockerContainerUptime = () => {
    const { container } = useDockerContainer()

    const startedAt = container?.State?.StartedAt ? new Date(container.State.StartedAt) : null;
    const now = new Date();
    const uptimeMs = startedAt ? now.getTime() - startedAt.getTime() : 0;

    const renderSignalIcon = () => {
        for (const key of Object.keys(signalMap)) {
            const signal = signalMap[key as keyof typeof signalMap];
            if (uptimeMs < signal.minimumUptimeMs) {
                const IconComponent = signal.icon;
                return <IconComponent size={18} color={signal.color} />;
            }
        }
        return null;
    }

    return (
        <div title={"Last Started At: " + (container?.State?.StartedAt || 'N/A')} className={"flex items-center space-x-1"}>
            {container?.State?.Status === "running" && container?.State?.StartedAt && (
                <>
                    <span className="text-xs text-muted-foreground">
                        up {formatDistanceToNow(container.State.StartedAt)}
                    </span>
                    <span>
                        {renderSignalIcon()}
                    </span>
                </>

            )}
            {container?.State?.Status !== "running" && (
                <span className="text-xs text-muted-foreground">
                    down {formatDistanceToNow(container.State.FinishedAt)}
                </span>
            )}
        </div>
    );
};

export default DockerContainerUptime;
