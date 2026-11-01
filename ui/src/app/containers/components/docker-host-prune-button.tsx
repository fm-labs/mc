import React from "react";
import {toast} from "react-toastify";
import {Loader2, Trash2} from "lucide-react";
import {Button} from "@/components/ui/button";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {DockerPruneScope, useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {cleanupStats, CountSize} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";

type PruneScopeMeta = {
    label: string
    description: string
}

const PRUNE_SCOPES: Record<DockerPruneScope, PruneScopeMeta> = {
    containers: {label: "Prune containers", description: "Removes all stopped containers."},
    images: {label: "Prune images", description: "Removes all images not used by any container (like `docker image prune -a`)."},
    volumes: {label: "Prune volumes", description: "Removes all volumes not used by any container. Data in these volumes is lost."},
    networks: {label: "Prune networks", description: "Removes all networks not used by any container."},
    buildcache: {label: "Prune build cache", description: "Removes all unused build cache."},
    system: {
        label: "Prune system",
        description: "Removes stopped containers, all unused images, unused volumes, unused networks and the build cache.",
    },
};

// Sum "SpaceReclaimed" and count deleted items across the per-resource prune results.
const summarizePruneResult = (result: Record<string, any> | undefined) => {
    let space = 0;
    let deleted = 0;
    Object.values(result ?? {}).forEach((r: any) => {
        if (!r || typeof r !== "object") return;
        space += typeof r.SpaceReclaimed === "number" ? r.SpaceReclaimed : 0;
        ["ContainersDeleted", "ImagesDeleted", "VolumesDeleted", "NetworksDeleted", "CachesDeleted"].forEach((k) => {
            deleted += Array.isArray(r[k]) ? r[k].length : 0;
        });
    });
    return {space, deleted};
};

const DockerHostPruneButton = ({scope, onPruned}: { scope: DockerPruneScope, onPruned?: () => void }) => {
    const {config, summary, pruneResources} = useContainerHost();
    const [open, setOpen] = React.useState(false);
    const [pending, setPending] = React.useState(false);
    const meta = PRUNE_SCOPES[scope];

    // Estimate what would be removed from the cached `docker system df` data.
    const estimate = React.useMemo((): CountSize | null => {
        if (!summary) return null;
        const c = cleanupStats(summary);
        switch (scope) {
            case "containers":
                return c.stoppedContainers;
            case "images":
                return c.unusedImages;
            case "volumes":
                return c.orphanVolumes;
            case "buildcache":
                return c.buildCache;
            case "system": {
                const parts = [c.stoppedContainers, c.unusedImages, c.orphanVolumes, c.buildCache];
                return {
                    count: parts.reduce((a, p) => a + p.count, 0),
                    size: parts.reduce((a, p) => a + p.size, 0),
                };
            }
            default:
                return null; // networks aren't part of `df`
        }
    }, [summary, scope]);

    const handlePrune = async () => {
        setPending(true);
        try {
            const result = await pruneResources(scope);
            const {space, deleted} = summarizePruneResult(result);
            toast.success(`${config.hostId}: removed ${deleted} item${deleted === 1 ? "" : "s"}, reclaimed ${formatBytes(space)}`);
            setOpen(false);
            onPruned?.();
        } catch (e: any) {
            toast.error(`Prune failed: ${e?.response?.data?.detail || e?.message || String(e)}`);
        } finally {
            setPending(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !pending && setOpen(v)}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10">
                    <Trash2/>
                    {meta.label}
                    {estimate && estimate.size > 0 && (
                        <span className="text-muted-foreground font-normal tabular-nums">
                            {formatBytes(estimate.size)}
                        </span>
                    )}
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{meta.label} on {config.hostId}?</DialogTitle>
                    <DialogDescription>{meta.description} This cannot be undone.</DialogDescription>
                </DialogHeader>
                {estimate && (
                    <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
                        <span className="font-medium tabular-nums">{estimate.count}</span> item{estimate.count === 1 ? "" : "s"},
                        about <span className="font-medium tabular-nums">{formatBytes(estimate.size)}</span> reclaimable
                        <span className="text-muted-foreground"> (estimate)</span>
                    </div>
                )}
                <DialogFooter>
                    <DialogClose asChild>
                        <Button variant="outline" disabled={pending}>Cancel</Button>
                    </DialogClose>
                    <Button variant="destructive" onClick={handlePrune} disabled={pending}>
                        {pending ? <Loader2 className="animate-spin"/> : <Trash2/>}
                        {pending ? "Pruning…" : "Prune"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default DockerHostPruneButton;
