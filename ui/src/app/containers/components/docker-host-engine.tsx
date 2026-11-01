import React from 'react';
import ReactJson from "@microlink/react-json-view";
import {AlertTriangle, Check, ChevronDown, Copy, Minus} from "lucide-react";
import {toast} from "react-toastify";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import {DiskBar, diskConfig, diskKeys, StatsSection, StatTile} from "@/app/containers/components/stats/stats-ui.tsx";
import {cleanupStats, DiskUsage, diskTotal, diskUsage} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {Badge} from "@/components/ui/badge.tsx";
import {Button} from "@/components/ui/button.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from "@/components/ui/collapsible.tsx";
import {useTheme} from "@/context/theme-provider.tsx";

type Row = [label: string, value: React.ReactNode]

const isEmpty = (v: unknown) =>
    v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);

const Bool = ({value}: { value?: boolean }) => value === undefined ? null : value
    ? <span className="inline-flex items-center gap-1 text-green-600"><Check className="size-3.5"/>Yes</span>
    : <span className="inline-flex items-center gap-1 text-muted-foreground"><Minus className="size-3.5"/>No</span>;

const Mono = ({children}: { children: React.ReactNode }) =>
    <span className="font-mono text-xs break-all">{children}</span>;

const BadgeList = ({items}: { items?: (string | null | undefined)[] | null }) => {
    const list = (items ?? []).filter(Boolean) as string[];
    if (list.length === 0) return null;
    return (
        <div className="flex flex-wrap justify-end gap-1">
            {list.map((i) => <Badge key={i} variant="secondary" className="font-mono">{i}</Badge>)}
        </div>
    );
};

// Label / value list; rows with empty values are skipped
const PropList = ({rows}: { rows: Row[] }) => {
    const visible = rows.filter(([, v]) => !isEmpty(v));
    if (visible.length === 0) return <p className="text-sm text-muted-foreground">No data.</p>;
    return (
        <dl className="divide-y text-sm">
            {visible.map(([label, value]) => (
                <div key={label} className="flex items-start justify-between gap-4 py-1.5">
                    <dt className="shrink-0 text-muted-foreground">{label}</dt>
                    <dd className="min-w-0 text-right font-medium">{value}</dd>
                </div>
            ))}
        </dl>
    );
};

const useIsDark = () => {
    const {theme} = useTheme();
    if (theme === "system") {
        return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return theme === "dark";
};

const RawJson = ({data, name}: { data: any, name: string }) => {
    const isDark = useIsDark();
    const copy = async () => {
        try {
            await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            toast.success(`Copied ${name} JSON`);
        } catch {
            toast.error("Could not copy to clipboard");
        }
    };
    if (!data) return <p className="text-sm text-muted-foreground">Not loaded yet.</p>;
    return (
        <div className="relative">
            <Button variant="outline" size="sm" className="absolute right-2 top-2 z-10" onClick={copy}>
                <Copy/> Copy
            </Button>
            <div className="max-h-[600px] overflow-auto rounded-md border p-3 text-xs">
                <ReactJson
                    src={data}
                    name={false}
                    collapsed={1}
                    theme={isDark ? "ocean" : "rjv-default"}
                    style={{backgroundColor: "transparent"}}
                    enableClipboard={true}
                    displayObjectSize={true}
                    displayDataTypes={false}
                    sortKeys={true}/>
            </div>
        </div>
    );
};

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
