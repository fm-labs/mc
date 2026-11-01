import React from "react";
import {Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle} from "@/components/ui/dialog.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {KeyValues, Mono, PropList, RawJson, Section} from "@/app/containers/components/docker-ui.tsx";
import {ContainerLink} from "@/app/containers/components/stats/stats-ui.tsx";
import {formatAge, formatBytes} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

export type VolumeMount = {
    id: string
    name: string
    state: string
    destination: string
    rw: boolean
}

// volume name -> containers mounting it (from `docker system df`)
export const useVolumeMounts = () => {
    const {summary} = useContainerHost();
    return React.useMemo(() => {
        const m: Record<string, VolumeMount[]> = {};
        ((summary?.Containers ?? []) as any[]).forEach((c) => {
            (c.Mounts ?? []).forEach((mount: any) => {
                if (mount.Type !== "volume" || !mount.Name) return;
                (m[mount.Name] ??= []).push({
                    id: c.Id,
                    name: (c.Names?.[0] ?? shortId(c.Id)).replace(/^\//, ""),
                    state: c.State,
                    destination: mount.Destination,
                    rw: mount.RW !== false,
                });
            });
        });
        return m;
    }, [summary]);
};

// Volumes created without a name get a 64-char hex id
export const isAnonymousVolume = (name?: string) => !!name && /^[0-9a-f]{64}$/.test(name);

// df reports -1 when the size wasn't computed
export const volumeSize = (v: any): number | undefined => {
    const s = v?.UsageData?.Size;
    return typeof s === "number" && s >= 0 ? s : undefined;
};

const DockerVolumeDetailsDialog = ({volume, mounts, open, onOpenChange}: {
    volume?: any
    mounts: VolumeMount[]
    open: boolean
    onOpenChange: (open: boolean) => void
}) => {
    const {config: hostConfig} = useContainerHost();
    if (!volume) return null;

    const labels = Object.entries(volume.Labels ?? {}) as [string, string][];
    const options = Object.entries(volume.Options ?? {}) as [string, string][];
    const created = volume.CreatedAt ? new Date(volume.CreatedAt) : undefined;
    const size = volumeSize(volume);
    const anonymous = isAnonymousVolume(volume.Name);
    const project = volume.Labels?.["com.docker.compose.project"];

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="flex max-h-[90vh] flex-col gap-4 sm:max-w-3xl">
                <DialogHeader className="text-left">
                    <div className="flex items-start gap-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-muted">
                            <AppIcon icon="container-volume" size={22}/>
                        </div>
                        <div className="min-w-0">
                            <DialogTitle className="break-all font-mono text-base">
                                {anonymous ? shortId(volume.Name) : volume.Name}
                            </DialogTitle>
                            <DialogDescription className="mt-1 flex flex-wrap items-center gap-2">
                                {mounts.length > 0
                                    ? <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">in use · {mounts.length}</Badge>
                                    : <Badge variant="outline">unused</Badge>}
                                {anonymous && <Badge variant="outline">anonymous</Badge>}
                                {project && <Badge variant="secondary">compose: {project}</Badge>}
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <div className="grid grid-cols-2 gap-3 rounded-lg border bg-muted/30 px-4 py-3 text-sm sm:grid-cols-4">
                    <div><div className="text-xs text-muted-foreground">Size</div><div className="font-semibold tabular-nums">{size !== undefined ? formatBytes(size) : "—"}</div></div>
                    <div title={created?.toLocaleString()}><div className="text-xs text-muted-foreground">Created</div><div className="font-semibold">{created ? formatAge(created.getTime()) : "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Driver</div><div className="font-semibold">{volume.Driver ?? "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Scope</div><div className="font-semibold">{volume.Scope ?? "—"}</div></div>
                </div>

                <Tabs defaultValue="overview" className="min-h-0 flex-1">
                    <TabsList>
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="labels">Labels ({labels.length})</TabsTrigger>
                        <TabsTrigger value="options">Options ({options.length})</TabsTrigger>
                        <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                    </TabsList>

                    <div className="mt-2 h-[min(28rem,55vh)] overflow-y-auto pr-1">
                        <TabsContent value="overview" className="space-y-5">
                            <Section title={`Mounted by (${mounts.length})`}>
                                {mounts.length > 0 ? (
                                    <ul className="divide-y rounded-md border text-sm">
                                        {mounts.map((m) => (
                                            <li key={`${m.id}-${m.destination}`} className="flex flex-wrap items-center justify-between gap-2 px-3 py-1.5">
                                                <div className="flex min-w-0 items-center gap-2">
                                                    <ContainerLink hostId={hostConfig.hostId} containerId={m.id} name={m.name}/>
                                                    <span className="text-muted-foreground">→</span>
                                                    <Mono>{m.destination}</Mono>
                                                    {!m.rw && <Badge variant="outline">read-only</Badge>}
                                                </div>
                                                <Badge variant="outline" className={m.state === "running" ? "text-green-600" : ""}>{m.state}</Badge>
                                            </li>
                                        ))}
                                    </ul>
                                ) : <p className="text-sm text-muted-foreground">No containers mount this volume. It will be removed by "Prune volumes".</p>}
                            </Section>
                            <Section title="Details">
                                <PropList rows={[
                                    ["Name", <Mono>{volume.Name}</Mono>],
                                    ["Mountpoint", volume.Mountpoint && <Mono>{volume.Mountpoint}</Mono>],
                                    ["Driver", volume.Driver],
                                    ["Scope", volume.Scope],
                                    ["Created", created?.toLocaleString()],
                                    ["Size", size !== undefined ? formatBytes(size) : undefined],
                                    ["Compose project", project],
                                    ["Compose volume", volume.Labels?.["com.docker.compose.volume"]],
                                ]}/>
                            </Section>
                        </TabsContent>

                        <TabsContent value="labels"><KeyValues entries={labels}/></TabsContent>
                        <TabsContent value="options"><KeyValues entries={options}/></TabsContent>
                        <TabsContent value="raw"><RawJson data={volume} name="volume"/></TabsContent>
                    </div>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
};

export default DockerVolumeDetailsDialog;
