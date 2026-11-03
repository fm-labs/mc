import React from 'react';
import {ColumnDef} from "@tanstack/react-table";
import {Info, Network} from "lucide-react";
import {Link} from "react-router";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import {Button} from "@/components/ui/button.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import DockerNetworkDetailsDialog, {
    isBuiltinNetwork,
    networkSubnets,
    useNetworkEndpoints,
} from "@/app/containers/components/docker-network-details-dialog.tsx";
import {ContainerLink} from "@/app/containers/components/stats/stats-ui.tsx";
import {formatAge} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

type NetworkFilter = "all" | "used" | "unused" | "builtin"

const Flag = ({children, className}: { children: React.ReactNode, className?: string }) => (
    <Badge variant="outline" className={`px-1.5 text-[11px] font-normal ${className ?? ""}`}>{children}</Badge>
)

const DockerHostNetworks = () => {
    const {fetchContainerData, config} = useContainerHost()
    const [networks, setNetworks] = React.useState<any[]>()
    const [selected, setSelected] = React.useState<any>()
    const [filter, setFilter] = React.useState<NetworkFilter>("all")
    const endpoints = useNetworkEndpoints(networks)

    const loadNetworks = React.useCallback(async (force?: boolean) => {
        const data = await fetchContainerData("networks", force).catch(() => {
            console.log("Failed to fetch networks")
            return []
        })
        setNetworks(data)
    }, [fetchContainerData])

    React.useEffect(() => {
        loadNetworks()
    }, [loadNetworks])

    const used = React.useCallback((n: any) => (endpoints[n.Id]?.length ?? 0) > 0, [endpoints])

    const counts = React.useMemo(() => {
        const list = networks ?? []
        return {
            all: list.length,
            used: list.filter(used).length,
            unused: list.filter((n) => !used(n)).length,
            builtin: list.filter(isBuiltinNetwork).length,
        }
    }, [networks, used])

    const visible = React.useMemo(() => {
        // custom networks first, then by name
        const list = [...(networks ?? [])].sort((a, b) =>
            Number(isBuiltinNetwork(a)) - Number(isBuiltinNetwork(b)) || (a.Name ?? "").localeCompare(b.Name ?? ""))
        switch (filter) {
            case "used": return list.filter(used)
            case "unused": return list.filter((n) => !used(n))
            case "builtin": return list.filter(isBuiltinNetwork)
            default: return list
        }
    }, [networks, used, filter])

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            id: "name",
            accessorKey: "Name",
            header: "Network",
            cell: ({row}) => {
                const n = row.original
                const project = n.Labels?.["com.docker.compose.project"]
                return (
                    <button type="button" onClick={() => setSelected(n)} title={n.Name}
                            className="flex min-w-0 items-center gap-2 text-left hover:underline">
                        <span className={`truncate font-medium ${isBuiltinNetwork(n) ? "text-muted-foreground" : ""}`}>{n.Name}</span>
                        {isBuiltinNetwork(n) && <Badge variant="outline">built-in</Badge>}
                        {project && <Badge variant="secondary">{project}</Badge>}
                    </button>
                )
            },
        },
        {
            id: "id",
            accessorKey: "Id",
            header: "ID",
            cell: ({row}) => <span className="font-mono text-xs text-muted-foreground" title={row.original.Id}>{shortId(row.original.Id)}</span>,
        },
        {
            id: "usage",
            accessorFn: (row) => endpoints[row.Id]?.length ?? 0,
            header: "Containers",
            cell: ({row}) => {
                const list = endpoints[row.original.Id] ?? []
                if (list.length === 0) return <Badge variant="outline" className="text-muted-foreground">unused</Badge>
                return (
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-sm">
                        <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">{list.length}</Badge>
                        {list.slice(0, 2).map((e) => (
                            <span key={e.id} title={[e.name, e.ipv4].filter(Boolean).join(" · ")} className="inline-flex items-center gap-1">
                                <span className={`size-1.5 rounded-full ${e.state === "running" ? "bg-green-500" : "bg-gray-400"}`}/>
                                <ContainerLink hostId={config.hostId} containerId={e.id} name={e.name}/>
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
            id: "subnet",
            accessorFn: (row) => networkSubnets(row).join(", "),
            header: "Subnet",
            cell: ({row}) => {
                const subnets = networkSubnets(row.original)
                return subnets.length > 0
                    ? <span className="font-mono text-xs">{subnets.join(", ")}</span>
                    : <span className="text-muted-foreground">—</span>
            },
        },
        {
            id: "flags",
            header: "Flags",
            enableSorting: false,
            cell: ({row}) => {
                const n = row.original
                return (
                    <div className="flex flex-wrap gap-1">
                        {n.Internal && <Flag className="text-amber-600">internal</Flag>}
                        {n.Attachable && <Flag>attachable</Flag>}
                        {n.Ingress && <Flag>ingress</Flag>}
                        {n.EnableIPv6 && <Flag>IPv6</Flag>}
                        {n.EnableIPv4 === false && <Flag>no IPv4</Flag>}
                    </div>
                )
            },
        },
        {
            id: "created",
            accessorKey: "Created",
            header: () => <div className="text-right">Created</div>,
            cell: ({row}) => {
                const d = row.original?.Created ? new Date(row.original.Created) : undefined
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
    ], [endpoints, config.hostId]);

    const filters: { key: NetworkFilter, label: string }[] = [
        {key: "all", label: "All"},
        {key: "used", label: "In use"},
        {key: "unused", label: "Unused"},
        {key: "builtin", label: "Built-in"},
    ]

    return (
        <div>
            <DockerHostHeader title={"Networks"} icon="container-network">
                <Button asChild variant="outline" size="sm">
                    <Link to={`/containers/network?host=${encodeURIComponent(config.hostId)}`}>
                        <Network className="size-4"/>View Network diagram
                    </Link>
                </Button>
            </DockerHostHeader>

            {networks === undefined ? (
                <p className="text-muted-foreground">Loading networks ...</p>
            ) : networks.length === 0 ? (
                <div className="rounded-lg border border-dashed px-4 py-10 text-center text-muted-foreground">No networks found.</div>
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
                            {visible.length} network{visible.length === 1 ? "" : "s"}
                        </span>
                    </div>
                    <DataTableGeneric columns={columns} data={visible} getRowId={(row: any) => row.Id}/>
                </>
            )}

            <DockerNetworkDetailsDialog network={selected} endpoints={selected ? endpoints[selected.Id] ?? [] : []}
                                        open={!!selected} onOpenChange={(o) => !o && setSelected(undefined)}/>
        </div>
    );
};

export default DockerHostNetworks;
