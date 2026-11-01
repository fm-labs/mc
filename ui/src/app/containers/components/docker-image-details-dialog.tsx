import React from "react";
import {Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle} from "@/components/ui/dialog.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {BadgeList, KeyValues, Mono, PropList, RawJson, Section} from "@/app/containers/components/docker-ui.tsx";
import {ContainerLink} from "@/app/containers/components/stats/stats-ui.tsx";
import {formatAge, formatBytes} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

// Containers (from `docker system df`) that use this image
export const useImageUsage = (imageId?: string) => {
    const {summary} = useContainerHost();
    return React.useMemo(() => {
        if (!imageId || !summary?.Containers) return [];
        return (summary.Containers as any[])
            .filter((c) => c.ImageID === imageId)
            .map((c) => ({id: c.Id as string, name: (c.Names?.[0] ?? shortId(c.Id)).replace(/^\//, ""), state: c.State as string}));
    }, [summary, imageId]);
};

export const imageRepoTag = (tag: string) => {
    const i = tag.lastIndexOf(":");
    return i > 0 && !tag.slice(i).includes("/") ? {repo: tag.slice(0, i), tag: tag.slice(i + 1)} : {repo: tag, tag: ""};
};

const CmdLine = ({value}: { value?: string[] | string | null }) => {
    if (!value || (Array.isArray(value) && value.length === 0)) return null;
    return (
        <code className="block rounded bg-muted px-2 py-1 text-left font-mono text-xs break-all">
            {Array.isArray(value) ? value.join(" ") : value}
        </code>
    );
};

const DockerImageDetailsDialog = ({image, open, onOpenChange}: {
    image?: any
    open: boolean
    onOpenChange: (open: boolean) => void
}) => {
    const {config: hostConfig} = useContainerHost();
    const usedBy = useImageUsage(image?.Id);
    if (!image) return null;

    const tags: string[] = image.RepoTags ?? [];
    const title = tags[0] ?? "<none>";
    const cfg = image.Config ?? {};
    const env: [string, string][] = (cfg.Env ?? []).map((e: string) => {
        const i = e.indexOf("=");
        return i >= 0 ? [e.slice(0, i), e.slice(i + 1)] : [e, ""];
    });
    const labels = Object.entries(cfg.Labels ?? {}) as [string, string][];
    const ports = Object.keys(cfg.ExposedPorts ?? {});
    const volumes = Object.keys(cfg.Volumes ?? {});
    const layers: string[] = image.RootFS?.Layers ?? [];
    const created = image.Created ? new Date(image.Created) : undefined;
    const platform = [image.Os, image.Architecture, image.Variant].filter(Boolean).join(" / ");

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="flex max-h-[90vh] flex-col gap-4 sm:max-w-3xl">
                <DialogHeader className="text-left">
                    <div className="flex items-start gap-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-muted">
                            <AppIcon icon="container-image" size={22}/>
                        </div>
                        <div className="min-w-0">
                            <DialogTitle className="break-all font-mono text-base">{title}</DialogTitle>
                            <DialogDescription className="mt-1 flex flex-wrap items-center gap-2">
                                <Mono>{shortId(image.Id)}</Mono>
                                {usedBy.length > 0
                                    ? <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">in use · {usedBy.length}</Badge>
                                    : <Badge variant="outline">unused</Badge>}
                                {tags.length === 0 && <Badge variant="outline" className="text-amber-600">dangling</Badge>}
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <div className="grid grid-cols-2 gap-3 rounded-lg border bg-muted/30 px-4 py-3 text-sm sm:grid-cols-4">
                    <div><div className="text-xs text-muted-foreground">Size</div><div className="font-semibold tabular-nums">{formatBytes(image.Size)}</div></div>
                    <div title={created?.toLocaleString()}><div className="text-xs text-muted-foreground">Created</div><div className="font-semibold">{created ? formatAge(created.getTime()) : "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Platform</div><div className="font-semibold">{platform || "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Layers</div><div className="font-semibold tabular-nums">{layers.length}</div></div>
                </div>

                <Tabs defaultValue="overview" className="min-h-0 flex-1">
                    <TabsList>
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="config">Config</TabsTrigger>
                        <TabsTrigger value="env">Env ({env.length})</TabsTrigger>
                        <TabsTrigger value="labels">Labels ({labels.length})</TabsTrigger>
                        <TabsTrigger value="layers">Layers</TabsTrigger>
                        <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                    </TabsList>

                    <div className="mt-2 h-[min(28rem,55vh)] overflow-y-auto pr-1">
                        <TabsContent value="overview" className="space-y-5">
                            <Section title="Tags">
                                {tags.length > 0 ? <div className="flex flex-wrap gap-1">{tags.map((t) => <Badge key={t} variant="secondary" className="font-mono">{t}</Badge>)}</div>
                                    : <p className="text-sm text-muted-foreground">No tags (dangling image).</p>}
                            </Section>
                            <Section title={`Used by (${usedBy.length})`}>
                                {usedBy.length > 0 ? (
                                    <ul className="divide-y rounded-md border text-sm">
                                        {usedBy.map((c) => (
                                            <li key={c.id} className="flex items-center justify-between px-3 py-1.5">
                                                <ContainerLink hostId={hostConfig.hostId} containerId={c.id} name={c.name}/>
                                                <Badge variant="outline" className={c.state === "running" ? "text-green-600" : ""}>{c.state}</Badge>
                                            </li>
                                        ))}
                                    </ul>
                                ) : <p className="text-sm text-muted-foreground">No containers use this image.</p>}
                            </Section>
                            <Section title="Details">
                                <PropList rows={[
                                    ["Image ID", <Mono>{image.Id}</Mono>],
                                    ["Digests", (image.RepoDigests ?? []).length > 0 &&
                                        <div className="space-y-0.5">{image.RepoDigests.map((d: string) => <div key={d}><Mono>{d}</Mono></div>)}</div>],
                                    ["Created", created?.toLocaleString()],
                                    ["Author", image.Author],
                                    ["Comment", image.Comment],
                                    ["Docker version", image.DockerVersion],
                                    ["Parent", image.Parent && <Mono>{shortId(image.Parent)}</Mono>],
                                    ["Storage driver", image.GraphDriver?.Name],
                                    ["Last tag time", image.Metadata?.LastTagTime && !image.Metadata.LastTagTime.startsWith("0001")
                                        ? new Date(image.Metadata.LastTagTime).toLocaleString() : undefined],
                                ]}/>
                            </Section>
                        </TabsContent>

                        <TabsContent value="config">
                            <PropList rows={[
                                ["Entrypoint", <CmdLine value={cfg.Entrypoint}/>],
                                ["Command", <CmdLine value={cfg.Cmd}/>],
                                ["Working dir", cfg.WorkingDir && <Mono>{cfg.WorkingDir}</Mono>],
                                ["User", cfg.User],
                                ["Exposed ports", ports.length > 0 && <BadgeList items={ports}/>],
                                ["Volumes", volumes.length > 0 && <BadgeList items={volumes}/>],
                                ["Stop signal", cfg.StopSignal],
                                ["Healthcheck", cfg.Healthcheck?.Test && <CmdLine value={cfg.Healthcheck.Test}/>],
                                ["Shell", <CmdLine value={cfg.Shell}/>],
                            ]}/>
                        </TabsContent>

                        <TabsContent value="env"><KeyValues entries={env}/></TabsContent>
                        <TabsContent value="labels"><KeyValues entries={labels}/></TabsContent>

                        <TabsContent value="layers">
                            {layers.length > 0 ? (
                                <ol className="divide-y rounded-md border font-mono text-xs">
                                    {layers.map((l, i) => (
                                        <li key={`${l}-${i}`} className="flex gap-3 px-3 py-1.5">
                                            <span className="w-6 shrink-0 text-right text-muted-foreground">{i + 1}</span>
                                            <span className="break-all">{l}</span>
                                        </li>
                                    ))}
                                </ol>
                            ) : <p className="text-sm text-muted-foreground">No layer info.</p>}
                        </TabsContent>

                        <TabsContent value="raw"><RawJson data={image} name="image"/></TabsContent>
                    </div>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
};

export default DockerImageDetailsDialog;
