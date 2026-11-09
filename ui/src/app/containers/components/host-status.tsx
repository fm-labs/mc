import {
    HostConnectionState,
    HostConnectionStatus,
    useContainerHosts,
} from "@/app/containers/components/container-hosts-provider.tsx";

// Two independent things are shown per host:
// - enabled/disabled: the user's choice, saved in the browser
// - the connection status on the backend: connected, connecting, disconnected, unreachable

const CONNECTION_STYLES: Record<HostConnectionState, { label: string, dot: string, text: string }> = {
    connected: {label: "Connected", dot: "bg-green-500", text: "text-green-700 dark:text-green-400"},
    connecting: {label: "Connecting", dot: "bg-amber-500 animate-pulse", text: "text-amber-700 dark:text-amber-400"},
    disconnected: {label: "Disconnected", dot: "bg-gray-400", text: "text-muted-foreground"},
    unreachable: {label: "Unreachable", dot: "bg-red-500", text: "text-red-700 dark:text-red-400"},
};

export type HostStatus = HostConnectionStatus & { enabled: boolean };

// eslint-disable-next-line react-refresh/only-export-components
export const useHostStatus = (hostId: string): HostStatus => {
    const {isHostEnabled, getHostStatus} = useContainerHosts();
    return {enabled: isHostEnabled(hostId), ...getHostStatus(hostId)};
};

// eslint-disable-next-line react-refresh/only-export-components
export const hostStatusTitle = ({enabled, state, error}: HostStatus) =>
    `${enabled ? "Enabled" : "Disabled"} · ${CONNECTION_STYLES[state].label}${error && state === "unreachable" ? `: ${error}` : ""}`;

/** Dot colored by connection status; dimmed when the host is disabled. Hover shows both. */
export const HostStatusDot = ({hostId, className}: { hostId: string, className?: string }) => {
    const status = useHostStatus(hostId);
    const title = hostStatusTitle(status);
    return (
        <span title={title} aria-label={title} role="img"
              className={`inline-block size-2 shrink-0 rounded-full ${CONNECTION_STYLES[status.state].dot} ${status.enabled ? "" : "opacity-50"} ${className ?? ""}`}/>
    );
};

/** Connection status with label, plus a "Disabled" tag when the user turned the host off */
export const HostStatusBadge = ({hostId, className}: { hostId: string, className?: string }) => {
    const status = useHostStatus(hostId);
    const style = CONNECTION_STYLES[status.state];
    return (
        <span className={`inline-flex items-center gap-1.5 text-xs ${className ?? ""}`} title={hostStatusTitle(status)}>
            {!status.enabled && (
                <span className="rounded border px-1.5 text-muted-foreground">Disabled</span>
            )}
            <span className={`inline-flex items-center gap-1.5 ${style.text}`}>
                <span className={`size-2 shrink-0 rounded-full ${style.dot}`}/>
                {style.label}
            </span>
        </span>
    );
};
