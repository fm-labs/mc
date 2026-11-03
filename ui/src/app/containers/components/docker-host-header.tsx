import React, {PropsWithChildren} from "react";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {formatBytes} from "@/app/containers/components/stats/format.ts";

type DockerHostHeaderProps = {
    title?: string
    icon?: string
}

const Stat = ({icon, value, label, className}: { icon: string, value: React.ReactNode, label: string, className?: string }) => (
    <div className="flex items-center gap-1.5">
        <AppIcon icon={icon} size={14}/>
        <span className={`font-medium tabular-nums text-foreground ${className ?? ""}`}>{value}</span>
        <span>{label}</span>
    </div>
);

// Status dot that doubles as a subtle connect/disconnect toggle
const ConnectionToggle = () => {
    const {enabled, setEnabled, summary} = useContainerHost();
    const status = enabled ? (summary ? "Connected" : "Connecting") : "Disconnected";
    const dot = enabled ? (summary ? "bg-green-500" : "bg-amber-500 animate-pulse") : "bg-gray-400";
    const action = enabled ? "Disconnect" : "Connect";

    return (
        <button type="button" onClick={() => setEnabled(!enabled)} title={`${status} – click to ${action.toLowerCase()}`}
                aria-label={`${action} host`}
                className="group ml-1 inline-flex items-center gap-1.5 rounded-full px-1.5 py-0.5 text-xs transition-colors hover:bg-muted">
            <span className={`size-2.5 rounded-full ${dot}`}/>
            <span className="group-hover:hidden">{status}</span>
            <span className="hidden text-foreground group-hover:inline">{action}</span>
        </button>
    );
};

const DockerHostHeader = ({title, icon, children}: PropsWithChildren<DockerHostHeaderProps>) => {
    const {config, host, info, summary, enabled} = useContainerHost();

    const diskUsed = React.useMemo(() => {
        if (!summary) return undefined;
        return typeof summary.LayersSize === "number" ? summary.LayersSize : undefined;
    }, [summary]);

    const engine = host?.properties?.engine || "container-host";

    return (
        <div className="mb-4 rounded-lg border bg-card px-4 py-3 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-muted">
                        <AppIcon icon={engine} size={22}/>
                    </div>
                    <div className="min-w-0">
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <span className="truncate font-medium">{config.hostId}</span>
                            <ConnectionToggle/>
                            {info?.ServerVersion && (
                                <span className="ml-1 rounded border px-1.5 text-xs">v{info.ServerVersion}</span>
                            )}
                        </div>
                        <h2 className="flex items-center gap-1 font-bold tracking-tight">
                            {icon && <AppIcon icon={icon} size={20} className="mr-1 text-muted-foreground"/>}
                            {title}
                        </h2>
                    </div>
                </div>
                {children && (
                    <div className="flex flex-wrap items-center gap-2">
                        {children}
                    </div>
                )}
            </div>

            {enabled && info && (
                <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 border-t pt-2 text-sm text-muted-foreground">
                    <Stat icon="container" value={info.Containers ?? 0} label="containers"/>
                    <span className="flex items-center gap-3">
                        <span><span className="font-medium tabular-nums text-green-600">{info.ContainersRunning ?? 0}</span> running</span>
                        <span><span className="font-medium tabular-nums text-amber-600">{info.ContainersPaused ?? 0}</span> paused</span>
                        <span><span className="font-medium tabular-nums">{info.ContainersStopped ?? 0}</span> stopped</span>
                    </span>
                    <span className="hidden h-4 w-px bg-border sm:block"/>
                    <Stat icon="container-image" value={info.Images ?? 0} label="images"/>
                    {summary?.Volumes && <Stat icon="container-volume" value={summary.Volumes.length} label="volumes"/>}
                    {diskUsed !== undefined && <span><span className="font-medium tabular-nums text-foreground">{formatBytes(diskUsed)}</span> image disk</span>}
                </div>
            )}
        </div>
    );
};

export default DockerHostHeader;
