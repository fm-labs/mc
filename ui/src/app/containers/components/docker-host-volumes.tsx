import React from 'react';
import {ColumnDef} from "@tanstack/react-table";
import {Info} from "lucide-react";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import {Button} from "@/components/ui/button.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import DockerVolumeDetailsDialog, {
    isAnonymousVolume,
    useVolumeMounts,
    volumeSize,
} from "@/app/containers/components/docker-volume-details-dialog.tsx";
import {ContainerLink} from "@/app/containers/components/stats/stats-ui.tsx";
import {formatAge, formatBytes} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

type VolumeFilter = "all" | "used" | "unused" | "anonymous"

const DockerHostVolumes = () => {
    const {summary, config} = useContainerHost()
    const mounts = useVolumeMounts()
    const [selected, setSelected] = React.useState<any>()
    const [filter, setFilter] = React.useState<VolumeFilter>("all")

    const volumes: any[] | undefined = summary?.Volumes
    const inUse = React.useCallback((v: any) => (mounts[v.Name]?.length ?? 0) > 0 || (v.UsageData?.RefCount ?? 0) > 0, [mounts])

    const counts = React.useMemo(() => {
        const list = volumes ?? []
        return {
            all: list.length,
            used: list.filter(inUse).length,
            unused: list.filter((v) => !inUse(v)).length,
            anonymous: list.filter((v) => isAnonymousVolume(v.Name)).length,
        }
    }, [volumes, inUse])

    const visible = React.useMemo(() => {
        const list = [...(volumes ?? [])].sort((a, b) =>
            Number(inUse(b)) - Number(inUse(a)) || (a.Name ?? "").localeCompare(b.Name ?? ""))
        switch (filter) {
            case "used": return list.filter(inUse)
            case "unused": return list.filter((v) => !inUse(v))
            case "anonymous": return list.filter((v) => isAnonymousVolume(v.Name))
            default: return list
        }
    }, [volumes, inUse, filter])

    const totalSize = React.useMemo(() => visible.reduce((a, v) => a + (volumeSize(v) ?? 0), 0), [visible])

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            id: "name",
            accessorKey: "Name",
            header: "Volume",
            cell: ({row}) => {
                const v = row.original
                const anonymous = isAnonymousVolume(v.Name)
                const project = v.Labels?.["com.docker.compose.project"]
                return (
                    <button type="button" onClick={() => setSelected(v)} title={v.Name}
                            className="flex min-w-0 items-center gap-2 text-left hover:underline">
                        <span className={`truncate ${anonymous ? "font-mono text-muted-foreground" : "font-medium"}`}>
                            {anonymous ? shortId(v.Name) : v.Name || "<none>"}
                        </span>
                        {anonymous && <Badge variant="outline">anonymous</Badge>}
                        {project && <Badge variant="secondary">{project}</Badge>}
                    </button>
                )
            },
        },
        {
            id: "usage",
            accessorFn: (row) => mounts[row.Name]?.length ?? row.UsageData?.RefCount ?? 0,
            header: "Status",
            cell: ({getValue}) => {
                const n = getValue() as number
                return n > 0
                    ? <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">in use · {n}</Badge>
                    : <Badge variant="outline" className="text-muted-foreground">unused</Badge>
            },
        },
        {
            id: "mountedBy",
            header: "Mounted by",
            enableSorting: false,
            cell: ({row}) => {
                const list = mounts[row.original.Name] ?? []
                if (list.length === 0) return <span className="text-muted-foreground">—</span>
                return (
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-sm">
                        {list.slice(0, 2).map((m) => (
                            <span key={`${m.id}-${m.destination}`} title={`${m.name} → ${m.destination}`} className="inline-flex items-center gap-1">
                                <span className={`size-1.5 rounded-full ${m.state === "running" ? "bg-green-500" : "bg-gray-400"}`}/>
                                <ContainerLink hostId={config.hostId} containerId={m.id} name={m.name}/>
                            </span>
                        ))}
                        {list.length > 2 && <span className="text-xs text-muted-foreground">+{list.length - 2}</span>}
                    </div>
                )
            },
        },
        {
            id: "driver",
            accessorKey: "Driver",
            header: "Driver",
            cell: ({row}) => <span className="text-sm text-muted-foreground">{row.original.Driver}{row.original.Scope && row.original.Scope !== "local" ? ` · ${row.original.Scope}` : ""}</span>,
        },
        {
            id: "size",
            accessorFn: (row) => volumeSize(row) ?? -1,
            header: () => <div className="text-right">Size</div>,
            cell: ({row}) => {
                const s = volumeSize(row.original)
                return <div className="text-right tabular-nums">{s !== undefined ? formatBytes(s) : <span className="text-muted-foreground">—</span>}</div>
            },
        },
        {
            id: "created",
            accessorKey: "CreatedAt",
            header: () => <div className="text-right">Created</div>,
            cell: ({row}) => {
                const d = row.original?.CreatedAt ? new Date(row.original.CreatedAt) : undefined
                return <div className="text-right text-sm text-muted-foreground" title={d?.toLocaleString()}>{d ? formatAge(d.getTime()) : "—"}</div>
            },
        },
        {
            id: "actions",
            header: "",
            enableSorting: false,
            cell: ({row}) => (
                <div className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => setSelected(row.original)} title="Show details">
                        <Info/> Details
                    </Button>
                </div>
            ),
        },
    ], [mounts, config.hostId]);

    const filters: { key: VolumeFilter, label: string }[] = [
        {key: "all", label: "All"},
        {key: "used", label: "In use"},
        {key: "unused", label: "Unused"},
        {key: "anonymous", label: "Anonymous"},
    ]

    return (
        <div>
            <DockerHostHeader title={"Volumes"} icon="container-volume" prune="volumes"/>

            {volumes === undefined ? (
                <p className="text-muted-foreground">Loading volumes ...</p>
            ) : volumes.length === 0 ? (
                <div className="rounded-lg border border-dashed px-4 py-10 text-center text-muted-foreground">No volumes found.</div>
            ) : (
                <>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                        <div className="inline-flex rounded-lg border bg-muted/40 p-0.5">
                            {filters.map((f) => (
                                <button key={f.key} type="button" onClick={() => setFilter(f.key)}
                                        className={`rounded-md px-3 py-1 text-sm transition-colors ${filter === f.key
                                            ? "bg-background font-medium shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                                    {f.label} <span className="tabular-nums text-muted-foreground">{counts[f.key]}</span>
                                </button>
                            ))}
                        </div>
                        <span className="text-sm text-muted-foreground">
                            {visible.length} volume{visible.length === 1 ? "" : "s"} · {formatBytes(totalSize)}
                        </span>
                    </div>
                    <DataTableGeneric columns={columns} data={visible} getRowId={(row: any) => row.Name}/>
                </>
            )}

            <DockerVolumeDetailsDialog volume={selected} mounts={selected ? mounts[selected.Name] ?? [] : []}
                                       open={!!selected} onOpenChange={(o) => !o && setSelected(undefined)}/>
        </div>
    );
};

export default DockerHostVolumes;
