import React, {PropsWithChildren} from "react";
import {Link} from "react-router";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {HostStatusBadge} from "@/app/containers/components/host-status.tsx";

type DockerHostHeaderProps = {
    title?: string
    icon?: string
}

const Stat = ({icon, value, label, to, className}: { icon: string, value: React.ReactNode, label: string, to: string, className?: string }) => (
    <Link to={to} className="flex items-center gap-1.5 hover:text-foreground hover:underline">
        <AppIcon icon={icon} size={14}/>
        <span className={`font-medium tabular-nums text-foreground ${className ?? ""}`}>{value}</span>
        <span>{label}</span>
    </Link>
);

// Connection status, plus the user's enable/disable toggle
const HostStatusControls = () => {
    const {enabled, setEnabled, config} = useContainerHost();
    return (
        <span className="ml-1 inline-flex items-center gap-1">
            <HostStatusBadge hostId={config.hostId}/>
            <button type="button" onClick={() => setEnabled(!enabled)}
                    title={enabled ? "Stop fetching data from this host" : "Connect and fetch data from this host"}
                    className="rounded px-1.5 py-0.5 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
                {enabled ? "Disable" : "Enable"}
            </button>
        </span>
    );
};

const DockerHostHeader = ({title, icon, children}: PropsWithChildren<DockerHostHeaderProps>) => {
    const {config, host, info, summary, enabled} = useContainerHost();

    const diskUsed = React.useMemo(() => {
        if (!summary) return undefined;
        return typeof summary.LayersSize === "number" ? summary.LayersSize : undefined;
    }, [summary]);

    const engine = host?.properties?.engine || "container-host";
    const base = `/containers/${encodeURIComponent(config.hostId)}`;

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
                            <HostStatusControls/>
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
                    <Stat icon="container" value={info.Containers ?? 0} label="containers" to={`${base}/container`}/>
                    <span className="flex items-center gap-3">
                        <span><span className="font-medium tabular-nums text-green-600">{info.ContainersRunning ?? 0}</span> running</span>
                        <span><span className="font-medium tabular-nums text-amber-600">{info.ContainersPaused ?? 0}</span> paused</span>
                        <span><span className="font-medium tabular-nums">{info.ContainersStopped ?? 0}</span> stopped</span>
                    </span>
                    <span className="hidden h-4 w-px bg-border sm:block"/>
                    <Stat icon="container-image" value={info.Images ?? 0} label="images" to={`${base}/images`}/>
                    {summary?.Volumes && <Stat icon="container-volume" value={summary.Volumes.length} label="volumes" to={`${base}/volumes`}/>}
                    {diskUsed !== undefined && <span><span className="font-medium tabular-nums text-foreground">{formatBytes(diskUsed)}</span> image disk</span>}
                </div>
            )}
        </div>
    );
};

export default DockerHostHeader;
