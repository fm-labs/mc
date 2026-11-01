import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import {ColumnDef} from "@tanstack/react-table";
import {Download, Info} from "lucide-react";
import {toast} from "react-toastify";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge.tsx";
import {RJSFSchema} from "@rjsf/utils";
import {SchemaFormDrawer} from "@/components/form/schema-form-drawer.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import DockerImageDetailsDialog, {imageRepoTag} from "@/app/containers/components/docker-image-details-dialog.tsx";
import {formatAge, formatBytes} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

const pullImageSchema: RJSFSchema = {
    title: "Pull Container Image",
    type: "object",
    required: ["image"],
    properties: {
        image: {
            type: "string",
            title: "Image Name",
            description: "Enter the name of the Docker image to pull (e.g., 'nginx:latest')"
        }
    }
}


const DockerHostImagePull = () => {
    const {pullImage} = useContainerHost()
    const [dialogOpen, setDialogOpen] = React.useState(false)

    const handlePull = async (formData: any) => {
        const imageName = (formData?.image || "").trim()
        if (imageName === "") {
            toast.error("Please enter an image name");
            return;
        }
        const id = toast.loading(`Pulling ${imageName} ...`)
        try {
            await pullImage(imageName)
            toast.update(id, {render: `Pulled ${imageName}`, type: "success", isLoading: false, autoClose: 3000})
            setDialogOpen(false)
        } catch (error: any) {
            console.error("Error pulling image:", error)
            toast.update(id, {
                render: `Error pulling ${imageName}: ${error?.response?.data?.detail || error?.message || error}`,
                type: "error", isLoading: false, autoClose: 5000,
            })
        }
    }

    return (
        <>
            <Button size="sm" onClick={() => setDialogOpen(!dialogOpen)}><Download/> Pull image</Button>
            <SchemaFormDrawer schema={pullImageSchema} open={dialogOpen}
                              onOpenChange={() => setDialogOpen(false)}
                              onSubmit={handlePull}/>
        </>
    )
}

type ImageFilter = "all" | "used" | "unused" | "dangling"

const ImageName = ({image, onOpen}: { image: any, onOpen: () => void }) => {
    const tags: string[] = image.RepoTags ?? []
    if (tags.length === 0) {
        return (
            <button type="button" onClick={onOpen} className="flex items-center gap-2 text-left hover:underline">
                <span className="font-mono text-muted-foreground">&lt;none&gt;</span>
                <Badge variant="outline" className="text-amber-600">dangling</Badge>
            </button>
        )
    }
    const {repo, tag} = imageRepoTag(tags[0])
    return (
        <button type="button" onClick={onOpen} className="flex min-w-0 items-center gap-2 text-left hover:underline"
                title={tags.join("\n")}>
            <span className="truncate font-medium">{repo}</span>
            {tag && <Badge variant="secondary" className="font-mono">{tag}</Badge>}
            {tags.length > 1 && <span className="text-xs text-muted-foreground">+{tags.length - 1}</span>}
        </button>
    )
}

const DockerHostImages = () => {
    const {fetchImages, summary} = useContainerHost()
    const [images, setImages] = React.useState<any[]>()
    const [selected, setSelected] = React.useState<any>()
    const [filter, setFilter] = React.useState<ImageFilter>("all")

    // image id -> number of containers using it
    const usage = React.useMemo(() => {
        const m: Record<string, number> = {}
        ;(summary?.Containers ?? []).forEach((c: any) => {
            if (c.ImageID) m[c.ImageID] = (m[c.ImageID] ?? 0) + 1
        })
        return m
    }, [summary])

    const counts = React.useMemo(() => {
        const list = images ?? []
        return {
            all: list.length,
            used: list.filter((i) => usage[i.Id]).length,
            unused: list.filter((i) => !usage[i.Id]).length,
            dangling: list.filter((i) => !(i.RepoTags ?? []).length).length,
        }
    }, [images, usage])

    const visible = React.useMemo(() => {
        const list = [...(images ?? [])].sort((a, b) => (b.Created ?? "").localeCompare(a.Created ?? ""))
        switch (filter) {
            case "used": return list.filter((i) => usage[i.Id])
            case "unused": return list.filter((i) => !usage[i.Id])
            case "dangling": return list.filter((i) => !(i.RepoTags ?? []).length)
            default: return list
        }
    }, [images, usage, filter])

    const totalSize = React.useMemo(() => visible.reduce((a, i) => a + (i.Size ?? 0), 0), [visible])

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            id: "name",
            accessorFn: (row) => row.RepoTags?.[0] ?? "",
            header: "Image",
            cell: ({row}) => <ImageName image={row.original} onOpen={() => setSelected(row.original)}/>,
        },
        {
            id: "id",
            accessorKey: "Id",
            header: "ID",
            cell: ({row}) => <span className="font-mono text-xs text-muted-foreground" title={row.original.Id}>{shortId(row.original.Id)}</span>,
        },
        {
            id: "usage",
            accessorFn: (row) => usage[row.Id] ?? 0,
            header: "Status",
            cell: ({getValue}) => {
                const n = getValue() as number
                return n > 0
                    ? <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">in use · {n}</Badge>
                    : <Badge variant="outline" className="text-muted-foreground">unused</Badge>
            },
        },
        {
            id: "platform",
            accessorFn: (row) => [row.Os, row.Architecture, row.Variant].filter(Boolean).join("/"),
            header: "Platform",
            cell: ({getValue}) => <span className="text-sm text-muted-foreground">{getValue() as string}</span>,
        },
        {
            id: "size",
            accessorKey: "Size",
            header: () => <div className="text-right">Size</div>,
            cell: ({row}) => <div className="text-right tabular-nums">{formatBytes(row.original?.Size)}</div>,
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
    ], [usage]);

    React.useEffect(() => {
        fetchImages().then(setImages).catch(() => setImages([]))
    }, [fetchImages])

    const filters: { key: ImageFilter, label: string }[] = [
        {key: "all", label: "All"},
        {key: "used", label: "In use"},
        {key: "unused", label: "Unused"},
        {key: "dangling", label: "Dangling"},
    ]

    return (
        <div>
            <DockerHostHeader title={"Images"} icon="container-image">
                <DockerHostImagePull/>
            </DockerHostHeader>

            {images === undefined ? (
                <p className="text-muted-foreground">Loading images ...</p>
            ) : images.length === 0 ? (
                <div className="rounded-lg border border-dashed px-4 py-10 text-center text-muted-foreground">No images found.</div>
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
                            {visible.length} image{visible.length === 1 ? "" : "s"} · {formatBytes(totalSize)}
                        </span>
                    </div>
                    <DataTableGeneric columns={columns} data={visible} getRowId={(row: any) => row.Id}/>
                </>
            )}

            <DockerImageDetailsDialog image={selected} open={!!selected} onOpenChange={(o) => !o && setSelected(undefined)}/>
        </div>
    );
};

export default DockerHostImages;
