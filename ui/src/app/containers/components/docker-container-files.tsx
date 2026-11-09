import React from "react";
import {
    IconChevronDown,
    IconChevronRight,
    IconFile,
    IconFolder,
    IconFolderOpen,
    IconLink,
    IconRefresh,
} from "@tabler/icons-react";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { formatBytes } from "@/app/containers/components/stats/format.ts";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";

type FileEntry = {
    name: string;
    path: string;
    type: "dir" | "file" | "link" | "other";
    is_dir: boolean;
    size: number | null;
    mtime: number | null;
};

type DirListing = {
    path: string;
    entries: FileEntry[];
    truncated: boolean;
};

type DirState = {
    loading: boolean;
    error?: string;
    listing?: DirListing;
};

const ROOT = "/";

const formatMtime = (mtime: number | null) =>
    mtime ? new Date(mtime * 1000).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" }) : "";

// File tree of a running container, from GET /containers/{host}/containers/{id}/files?path=...
// Directories are loaded when they are expanded.
const DockerContainerFiles = () => {
    const { container, hostId } = useDockerContainer();
    const { api } = useApi();

    const [dirs, setDirs] = React.useState<Record<string, DirState>>({});
    const [expanded, setExpanded] = React.useState<Set<string>>(new Set([ROOT]));
    const [root, setRoot] = React.useState(ROOT);
    const [rootInput, setRootInput] = React.useState(ROOT);

    const isRunning = container?.State?.Running === true;

    const loadDir = React.useCallback((path: string) => {
        if (!container?.Id) {
            return;
        }
        setDirs((prev) => ({ ...prev, [path]: { ...prev[path], loading: true, error: undefined } }));
        api.get(`/api/containers/${hostId}/containers/${container.Id}/files`, { params: { path } })
            .then((data: DirListing) => {
                setDirs((prev) => ({ ...prev, [path]: { loading: false, listing: data } }));
            })
            .catch((err: any) => {
                const error = err?.response?.data?.detail || err?.message || "Unknown error";
                setDirs((prev) => ({ ...prev, [path]: { loading: false, error } }));
            });
    }, [api, hostId, container?.Id]);

    // start over when the container changes
    React.useEffect(() => {
        setDirs({});
        setExpanded(new Set([ROOT]));
        setRoot(ROOT);
        setRootInput(ROOT);
        if (isRunning) {
            loadDir(ROOT);
        }
    }, [hostId, container?.Id, isRunning]);

    const toggleDir = (path: string) => {
        const isOpen = expanded.has(path);
        setExpanded((prev) => {
            const next = new Set(prev);
            if (isOpen) {
                next.delete(path);
            } else {
                next.add(path);
            }
            return next;
        });
        if (!isOpen && !dirs[path]?.listing && !dirs[path]?.loading) {
            loadDir(path);
        }
    };

    const openRoot = (path: string) => {
        const p = path.trim() || ROOT;
        setRoot(p);
        setExpanded((prev) => new Set(prev).add(p));
        loadDir(p);
    };

    // reload every open directory, drop the others
    const refresh = () => {
        setDirs({});
        expanded.forEach((path) => loadDir(path));
        if (!expanded.has(root)) {
            setExpanded((prev) => new Set(prev).add(root));
            loadDir(root);
        }
    };

    if (!isRunning) {
        return <div className={"p-2 text-muted-foreground"}>The container is not running.</div>;
    }

    const anyLoading = Object.values(dirs).some((d) => d.loading);

    const renderChildren = (path: string, depth: number): React.ReactNode => {
        const state = dirs[path];
        const indent = { paddingLeft: `${depth * 0.875 + 0.25}rem` };
        if (!state || (state.loading && !state.listing)) {
            return <div className={"text-muted-foreground"} style={indent}>Loading ...</div>;
        }
        if (state.error) {
            return <div className={"text-destructive"} style={indent}>{state.error}</div>;
        }
        const listing = state.listing!;
        return (
            <>
                {listing.entries.length === 0 && (
                    <div className={"text-muted-foreground"} style={indent}>Empty</div>
                )}
                {listing.entries.map((entry) => renderEntry(entry, depth))}
                {listing.truncated && (
                    <div className={"text-muted-foreground"} style={indent}>
                        Showing the first {listing.entries.length} entries.
                    </div>
                )}
            </>
        );
    };

    const renderEntry = (entry: FileEntry, depth: number): React.ReactNode => {
        const isOpen = entry.is_dir && expanded.has(entry.path);
        const Chevron = isOpen ? IconChevronDown : IconChevronRight;
        const Icon = entry.is_dir ? (isOpen ? IconFolderOpen : IconFolder) : IconFile;
        return (
            <React.Fragment key={entry.path}>
                <div className={"flex h-5 items-center gap-1 rounded-sm pr-1 hover:bg-muted"
                    + (entry.is_dir ? " cursor-pointer" : "")}
                     style={{ paddingLeft: `${depth * 0.875}rem` }}
                     title={entry.path}
                     onClick={entry.is_dir ? () => toggleDir(entry.path) : undefined}>
                    {entry.is_dir
                        ? <Chevron size={"0.9em"} className={"shrink-0 text-muted-foreground"} />
                        : <span className={"w-[0.9em] shrink-0"} />}
                    <Icon size={"1em"} className={"shrink-0 " + (entry.is_dir ? "text-primary" : "text-muted-foreground")} />
                    <span className={"truncate"}>{entry.name}</span>
                    {entry.type === "link" && <IconLink size={"0.9em"} className={"shrink-0 text-muted-foreground"} />}
                    <span className={"ml-auto shrink-0 pl-3 text-muted-foreground tabular-nums"}>
                        {entry.type === "file" && entry.size !== null ? formatBytes(entry.size) : ""}
                    </span>
                    <span className={"hidden w-36 shrink-0 text-right text-muted-foreground tabular-nums md:inline"}>
                        {formatMtime(entry.mtime)}
                    </span>
                </div>
                {isOpen && renderChildren(entry.path, depth + 1)}
            </React.Fragment>
        );
    };

    return (
        <div className={"space-y-1.5"}>
            <form className={"flex items-center gap-2"}
                  onSubmit={(e) => {
                      e.preventDefault();
                      openRoot(rootInput);
                  }}>
                <Input className={"h-7 max-w-[300px] font-mono text-xs"}
                       placeholder={"/"}
                       value={rootInput}
                       onChange={(e) => setRootInput(e.target.value)} />
                <Button type={"submit"} variant={"outline"} size={"sm"} className={"h-7"}>Open</Button>
                <Button type={"button"} variant={"outline"} size={"sm"} className={"h-7"} disabled={anyLoading} onClick={refresh}>
                    <IconRefresh size={"1em"} className={anyLoading ? "animate-spin" : ""} /> Refresh
                </Button>
            </form>

            <div className={"rounded border px-1 py-0.5 font-mono text-xs leading-5"}>
                <div className={"flex h-5 items-center gap-1 px-1 font-semibold"}>
                    <IconFolderOpen size={"1em"} className={"shrink-0 text-primary"} />
                    {dirs[root]?.listing?.path ?? root}
                </div>
                {renderChildren(root, 1)}
            </div>
        </div>
    );
};

export default DockerContainerFiles;
