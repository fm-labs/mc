import React from 'react';
import {AlertTriangle, ChevronDown} from "lucide-react";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import {DiskBar, diskConfig, diskKeys, StatsSection, StatTile} from "@/app/containers/components/stats/stats-ui.tsx";
import {cleanupStats, DiskUsage, diskTotal, diskUsage} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {Badge} from "@/components/ui/badge.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from "@/components/ui/collapsible.tsx";
import {BadgeList, Bool, Mono, PropList, RawJson, Row} from "@/app/containers/components/docker-ui.tsx";
import DockerHostPruneButton, {PRUNE_SCOPES} from "@/app/containers/components/docker-host-prune-button.tsx";
import {DockerPruneScope} from "@/app/containers/components/container-host-provider.tsx";

const MAINTENANCE_SCOPES: DockerPruneScope[] = ["containers", "images", "volumes", "networks", "buildcache", "system"];

const MaintenanceSection = () => (
    <StatsSection title="Maintenance" description="Free up disk space by removing unused resources. Sizes are estimates.">
        <div className="divide-y">
            {MAINTENANCE_SCOPES.map((scope) => (
                <div key={scope} className="flex flex-wrap items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
                    <div className="min-w-0">
                        <div className={`text-sm font-medium ${scope === "system" ? "text-destructive" : ""}`}>
                            {PRUNE_SCOPES[scope].label}
                        </div>
                        <div className="text-xs text-muted-foreground">{PRUNE_SCOPES[scope].description}</div>
                    </div>
                    <DockerHostPruneButton scope={scope}/>
                </div>
            ))}
        </div>
    </StatsSection>
);

const DockerHostEngine = () => {
    const {summary, info: rawInfo} = useContainerHost();
    const info: any = rawInfo ?? {};
    const [rawOpen, setRawOpen] = React.useState(false);

    const disk = React.useMemo(() => summary ? diskUsage(summary) : undefined, [summary]);

    const reclaimable = React.useMemo((): DiskUsage | undefined => {
        if (!summary) return undefined;
        const c = cleanupStats(summary);
        return {
            images: c.unusedImages.size,
            containers: c.stoppedContainers.size,
            volumes: c.orphanVolumes.size,
            buildCache: c.buildCache.size,
        };
    }, [summary]);

    const driverStatus: Row[] = (info.DriverStatus ?? []).map(([k, v]: [string, string]) => [k, <Mono>{v}</Mono>]);
    const runtimes = Object.keys(info.Runtimes ?? {});
    const swarm = info.Swarm ?? {};
    const swarmActive = swarm.LocalNodeState && swarm.LocalNodeState !== "inactive";
    const plugins = info.Plugins ?? {};
    const registry = info.RegistryConfig ?? {};
    const mirrors: string[] = Object.values(registry.IndexConfigs ?? {}).flatMap((c: any) => c?.Mirrors ?? []);
    const warnings: string[] = info.Warnings ?? [];

    return (
        <div className="space-y-4">
            <DockerHostHeader title={"Engine"} icon="info" prune={["buildcache", "system"]}/>

            {!rawInfo && !summary && <p className="text-sm text-muted-foreground">Loading engine info ...</p>}

            {rawInfo && (
                <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
                    <StatTile icon="container-host" label="Engine" value={info.ServerVersion ?? "—"}
                              sub={[info.OSType, info.Architecture].filter(Boolean).join(" / ")}/>
                    <StatTile icon="info" label="CPUs" value={info.NCPU ?? "—"}/>
                    <StatTile icon="info" label="Memory" value={info.MemTotal ? formatBytes(info.MemTotal) : "—"}/>
                    <StatTile icon="container" label="Containers" value={info.Containers ?? 0}
                              sub={`${info.ContainersRunning ?? 0} running · ${info.ContainersPaused ?? 0} paused · ${info.ContainersStopped ?? 0} stopped`}/>
                    <StatTile icon="container-image" label="Images" value={info.Images ?? 0}/>
                    <StatTile icon="container-volume" label="Disk used" value={disk ? formatBytes(diskTotal(disk)) : "—"}
                              sub={reclaimable && diskTotal(reclaimable) > 0 ? `${formatBytes(diskTotal(reclaimable))} reclaimable` : undefined}
                              tone={reclaimable && disk && diskTotal(reclaimable) > diskTotal(disk) / 2 ? "warn" : undefined}/>
                </div>
            )}

            {warnings.length > 0 && (
                <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
                    <div className="mb-1 flex items-center gap-2 font-medium text-amber-700 dark:text-amber-400">
                        <AlertTriangle className="size-4"/> {warnings.length} engine warning{warnings.length === 1 ? "" : "s"}
                    </div>
                    <ul className="list-disc space-y-0.5 pl-6 text-muted-foreground">
                        {warnings.map((w) => <li key={w}>{w}</li>)}
                    </ul>
                </div>
            )}

            {disk && reclaimable && (
                <StatsSection title="Disk usage" description="Same as `docker system df`">
                    <DiskBar disk={disk}/>
                    <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
                        {diskKeys.map((k) => (
                            <div key={k} className="text-sm">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <span className="size-2.5 rounded-[2px]" style={{backgroundColor: diskConfig[k].color}}/>
                                    {diskConfig[k].label}
                                </div>
                                <div className="text-lg font-semibold tabular-nums">{formatBytes(disk[k])}</div>
                                <div className="text-xs text-muted-foreground tabular-nums">
                                    {formatBytes(reclaimable[k])} reclaimable
                                </div>
                            </div>
                        ))}
                    </div>
                </StatsSection>
            )}

            {rawInfo && (
                <div className="grid gap-4 lg:grid-cols-2">
                    <StatsSection title="System" description={info.Name}>
                        <PropList rows={[
                            ["Operating system", info.OperatingSystem],
                            ["OS type", info.OSType],
                            ["Architecture", info.Architecture],
                            ["Kernel", <Mono>{info.KernelVersion}</Mono>],
                            ["CPUs", info.NCPU],
                            ["Memory", info.MemTotal ? formatBytes(info.MemTotal) : undefined],
                            ["System time", info.SystemTime ? new Date(info.SystemTime).toLocaleString() : undefined],
                            ["HTTP proxy", info.HttpProxy && <Mono>{info.HttpProxy}</Mono>],
                            ["HTTPS proxy", info.HttpsProxy && <Mono>{info.HttpsProxy}</Mono>],
                            ["No proxy", info.NoProxy && <Mono>{info.NoProxy}</Mono>],
                            ["Engine ID", info.ID && <Mono>{info.ID}</Mono>],
                        ]}/>
                    </StatsSection>

                    <StatsSection title="Engine" description={info.ServerVersion && `Docker ${info.ServerVersion}`}>
                        <PropList rows={[
                            ["Root dir", <Mono>{info.DockerRootDir}</Mono>],
                            ["Default runtime", info.DefaultRuntime],
                            ["Runtimes", runtimes.length > 0 && <BadgeList items={runtimes}/>],
                            ["Cgroup", [info.CgroupDriver, info.CgroupVersion && `v${info.CgroupVersion}`].filter(Boolean).join(" ")],
                            ["Logging driver", info.LoggingDriver],
                            ["Live restore", <Bool value={info.LiveRestoreEnabled}/>],
                            ["Experimental", <Bool value={info.ExperimentalBuild}/>],
                            ["Debug", <Bool value={info.Debug}/>],
                            ["containerd", info.ContainerdCommit?.ID && <Mono>{info.ContainerdCommit.ID.slice(0, 12)}</Mono>],
                            ["runc", info.RuncCommit?.ID && <Mono>{info.RuncCommit.ID.slice(0, 12)}</Mono>],
                        ]}/>
                    </StatsSection>

                    <StatsSection title="Storage" description={info.Driver && `Driver: ${info.Driver}`}>
                        <PropList rows={[["Storage driver", info.Driver], ...driverStatus]}/>
                    </StatsSection>

                    <StatsSection title="Security & plugins">
                        <PropList rows={[
                            ["Security options", <BadgeList items={(info.SecurityOptions ?? []).map((s: string) => s.replace(/^name=/, ""))}/>],
                            ["Volume plugins", <BadgeList items={plugins.Volume}/>],
                            ["Network plugins", <BadgeList items={plugins.Network}/>],
                            ["Log plugins", <BadgeList items={plugins.Log}/>],
                            ["Authorization", <BadgeList items={plugins.Authorization}/>],
                        ]}/>
                    </StatsSection>

                    <StatsSection title="Registry">
                        <PropList rows={[
                            ["Index server", info.IndexServerAddress && <Mono>{info.IndexServerAddress}</Mono>],
                            ["Mirrors", <BadgeList items={mirrors}/>],
                            ["Insecure registries", <BadgeList items={registry.InsecureRegistryCIDRs}/>],
                        ]}/>
                    </StatsSection>

                    <StatsSection title="Swarm"
                                  description={<Badge variant={swarmActive ? "default" : "outline"}>{swarm.LocalNodeState ?? "unknown"}</Badge>}>
                        {swarmActive ? (
                            <PropList rows={[
                                ["Node ID", swarm.NodeID && <Mono>{swarm.NodeID}</Mono>],
                                ["Node address", swarm.NodeAddr],
                                ["Manager", <Bool value={swarm.ControlAvailable}/>],
                                ["Managers", swarm.Managers],
                                ["Nodes", swarm.Nodes],
                                ["Cluster ID", swarm.Cluster?.ID && <Mono>{swarm.Cluster.ID}</Mono>],
                            ]}/>
                        ) : <p className="text-sm text-muted-foreground">This engine is not part of a swarm.</p>}
                    </StatsSection>
                </div>
            )}

            {rawInfo && <MaintenanceSection/>}

            <Collapsible open={rawOpen} onOpenChange={setRawOpen} className="rounded-lg border bg-card">
                <CollapsibleTrigger asChild>
                    <button className="flex w-full items-center justify-between px-4 py-3 text-left">
                        <span>
                            <span className="font-semibold">Raw data</span>
                            <span className="ml-2 text-sm text-muted-foreground">Full JSON from the engine API</span>
                        </span>
                        <ChevronDown className={`size-4 transition-transform ${rawOpen ? "rotate-180" : ""}`}/>
                    </button>
                </CollapsibleTrigger>
                <CollapsibleContent className="px-4 pb-4">
                    <Tabs defaultValue="info">
                        <TabsList>
                            <TabsTrigger value="info">Info</TabsTrigger>
                            <TabsTrigger value="df">Disk usage (df)</TabsTrigger>
                        </TabsList>
                        <TabsContent value="info"><RawJson data={rawInfo} name="info"/></TabsContent>
                        <TabsContent value="df"><RawJson data={summary} name="disk usage"/></TabsContent>
                    </Tabs>
                </CollapsibleContent>
            </Collapsible>
        </div>
    );
};

export default DockerHostEngine;
