import React from "react";
import {
    IconChevronDown,
    IconChevronRight,
    IconFile,
    IconFolder,
    IconFolderOpen,
    IconLink,
    IconRefresh,
    IconX,
} from "@tabler/icons-react";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { formatBytes } from "@/app/containers/components/stats/format.ts";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Toggle } from "@/components/ui/toggle.tsx";

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

type FileContent = {
    path: string;
    size: number;
    content: string | null;
    truncated: boolean;
    binary: boolean;
};

type OpenFile = {
    path: string;
    loading: boolean;
    error?: string;
    file?: FileContent;
};

// `docker diff` change kinds
type DiffKind = 0 | 1 | 2;
type DiffEntry = { Path: string; Kind: DiffKind };

const DIFF_KINDS: Record<DiffKind, { letter: string; label: string; className: string }> = {
    0: { letter: "M", label: "changed", className: "text-amber-600 dark:text-amber-400" },
    1: { letter: "A", label: "added", className: "text-emerald-600 dark:text-emerald-400" },
    2: { letter: "D", label: "deleted", className: "text-red-600 dark:text-red-400" },
};

const ROOT = "/";

const parentPath = (path: string) => {
    const i = path.lastIndexOf("/");
    return i <= 0 ? ROOT : path.slice(0, i);
};

const formatMtime = (mtime: number | null) =>
    mtime ? new Date(mtime * 1000).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" }) : "";

// File tree of a running container, from GET /containers/{host}/containers/{id}/files?path=...
// Directories are loaded when they are expanded. Changes compared to the image (`docker diff`, from .../diff)
// are marked in the tree, and deleted files are shown struck through.
const DockerContainerFiles = () => {
    const { container, hostId } = useDockerContainer();
    const { api } = useApi();

    const [dirs, setDirs] = React.useState<Record<string, DirState>>({});
    const [expanded, setExpanded] = React.useState<Set<string>>(new Set([ROOT]));
    const [root, setRoot] = React.useState(ROOT);
    const [rootInput, setRootInput] = React.useState(ROOT);

    const [diff, setDiff] = React.useState<Map<string, DiffKind>>(new Map());
    const [diffError, setDiffError] = React.useState<string>();
    const [changesOnly, setChangesOnly] = React.useState(false);
    const [openFile, setOpenFile] = React.useState<OpenFile>();

    const isRunning = container?.State?.Running === true;

    const loadDiff = React.useCallback(() => {
        if (!container?.Id) {
            return;
        }
        setDiffError(undefined);
        api.get(`/api/containers/${hostId}/containers/${container.Id}/diff`)
            .then((data: DiffEntry[]) => setDiff(new Map((data || []).map((d) => [d.Path, d.Kind]))))
            .catch((err: any) => {
                setDiff(new Map());
                setDiffError(err?.response?.data?.detail || err?.message || "Unknown error");
            });
    }, [api, hostId, container?.Id]);

    // directories with changes somewhere below them, and deleted entries per directory
    const { changedDirs, deletedByDir, counts } = React.useMemo(() => {
        const changedDirs = new Set<string>();
        const deletedByDir = new Map<string, string[]>();
        const counts: Record<DiffKind, number> = { 0: 0, 1: 0, 2: 0 };
        diff.forEach((kind, path) => {
            counts[kind]++;
            for (let p = parentPath(path); ; p = parentPath(p)) {
                changedDirs.add(p);
                if (p === ROOT) break;
            }
            if (kind === 2) {
                const dir = parentPath(path);
                deletedByDir.set(dir, [...(deletedByDir.get(dir) || []), path]);
            }
        });
        return { changedDirs, deletedByDir, counts };
    }, [diff]);

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

    const loadFile = React.useCallback((path: string) => {
        if (!container?.Id) {
            return;
        }
        setOpenFile({ path, loading: true });
        api.get(`/api/containers/${hostId}/containers/${container.Id}/file`, { params: { path } })
            .then((data: FileContent) => {
                setOpenFile((prev) => (prev?.path === path ? { path, loading: false, file: data } : prev));
            })
            .catch((err: any) => {
                const error = err?.response?.data?.detail || err?.message || "Unknown error";
                setOpenFile((prev) => (prev?.path === path ? { path, loading: false, error } : prev));
            });
    }, [api, hostId, container?.Id]);

    // start over when the container changes
    React.useEffect(() => {
        setDirs({});
        setExpanded(new Set([ROOT]));
        setRoot(ROOT);
        setRootInput(ROOT);
        setDiff(new Map());
        setOpenFile(undefined);
        if (isRunning) {
            loadDir(ROOT);
            loadDiff();
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
        loadDiff();
        if (openFile) {
            loadFile(openFile.path);
        }
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
        const listed = new Set(listing.entries.map((e) => e.path));
        const deleted: FileEntry[] = (deletedByDir.get(listing.path) || [])
            .filter((p) => !listed.has(p))
            .map((p) => ({ name: p.slice(p.lastIndexOf("/") + 1), path: p, type: "other", is_dir: false, size: null, mtime: null }));
        const entries = [...listing.entries, ...deleted]
            .filter((e) => !changesOnly || diff.has(e.path) || changedDirs.has(e.path));
        return (
            <>
                {entries.length === 0 && (
                    <div className={"text-muted-foreground"} style={indent}>{changesOnly ? "No changes" : "Empty"}</div>
                )}
                {entries.map((entry) => renderEntry(entry, depth))}
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
        const kind = diff.get(entry.path);
        const change = kind !== undefined ? DIFF_KINDS[kind] : undefined;
        const isDeleted = kind === 2;
        const hasChangesBelow = entry.is_dir && changedDirs.has(entry.path);
        // files and links to files can be opened, deleted files can't
        const canOpen = !entry.is_dir && !isDeleted && (entry.type === "file" || entry.type === "link");
        const isSelected = openFile?.path === entry.path;
        const onClick = entry.is_dir
            ? () => toggleDir(entry.path)
            : canOpen ? () => loadFile(entry.path) : undefined;
        return (
            <React.Fragment key={entry.path}>
                <div className={"flex h-5 items-center gap-1 rounded-sm pr-1 hover:bg-muted"
                    + (onClick ? " cursor-pointer" : "")
                    + (isSelected ? " bg-muted" : "")}
                     style={{ paddingLeft: `${depth * 0.875}rem` }}
                     title={change ? `${entry.path} (${change.label})` : entry.path}
                     onClick={onClick}>
                    {entry.is_dir
                        ? <Chevron size={"0.9em"} className={"shrink-0 text-muted-foreground"} />
                        : <span className={"w-[0.9em] shrink-0"} />}
                    <Icon size={"1em"} className={"shrink-0 " + (entry.is_dir ? "text-primary" : "text-muted-foreground")} />
                    <span className={"truncate " + (change ? change.className : "") + (isDeleted ? " line-through" : "")}>
                        {entry.name}
                    </span>
                    {entry.type === "link" && <IconLink size={"0.9em"} className={"shrink-0 text-muted-foreground"} />}
                    {!change && hasChangesBelow && (
                        <span className={"shrink-0 text-amber-600 dark:text-amber-400"} title={"Contains changes"}>•</span>
                    )}
                    <span className={"ml-auto shrink-0 pl-3 text-muted-foreground tabular-nums"}>
                        {entry.type === "file" && entry.size !== null ? formatBytes(entry.size) : ""}
                    </span>
                    <span className={"hidden w-36 shrink-0 text-right text-muted-foreground tabular-nums md:inline"}>
                        {formatMtime(entry.mtime)}
                    </span>
                    <span className={"w-3 shrink-0 text-center font-semibold " + (change?.className ?? "")}>
                        {change?.letter}
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
                <Toggle variant={"outline"} size={"sm"} className={"h-7 text-xs"}
                        pressed={changesOnly} onPressedChange={setChangesOnly}>
                    Changes only
                </Toggle>
                <span className={"ml-auto flex gap-2 text-xs text-muted-foreground"}>
                    {diffError
                        ? <span className={"text-destructive"} title={diffError}>Changes unavailable</span>
                        : ([1, 0, 2] as DiffKind[]).map((k) => (
                            <span key={k} className={counts[k] ? DIFF_KINDS[k].className : ""}>
                                {counts[k]} {DIFF_KINDS[k].label}
                            </span>
                        ))}
                </span>
            </form>

            <div className={"grid items-start gap-2" + (openFile ? " md:grid-cols-2" : "")}>
                <div className={"min-w-0 rounded border px-1 py-0.5 font-mono text-xs leading-5"}>
                    <div className={"flex h-5 items-center gap-1 px-1 font-semibold"}>
                        <IconFolderOpen size={"1em"} className={"shrink-0 text-primary"} />
                        {dirs[root]?.listing?.path ?? root}
                    </div>
                    {renderChildren(root, 1)}
                </div>
                {openFile && <FileViewer openFile={openFile} onClose={() => setOpenFile(undefined)} />}
            </div>
        </div>
    );
};

const FileViewer = ({ openFile, onClose }: { openFile: OpenFile; onClose: () => void }) => {
    const { file } = openFile;
    return (
        <div className={"min-w-0 rounded border text-xs md:sticky md:top-2"}>
            <div className={"flex h-7 items-center gap-2 border-b px-2"}>
                <span className={"truncate font-mono font-semibold"} title={openFile.path}>{openFile.path}</span>
                {file && (
                    <span className={"shrink-0 text-muted-foreground tabular-nums"}>
                        {formatBytes(file.size)}{file.truncated && " · first 1 MiB"}
                    </span>
                )}
                <Button variant={"ghost"} size={"icon"} className={"ml-auto size-5 shrink-0"}
                        title={"Close"} onClick={onClose}>
                    <IconX size={"1em"} />
                </Button>
            </div>
            {openFile.loading && <div className={"p-2 text-muted-foreground"}>Loading ...</div>}
            {openFile.error && <div className={"p-2 text-destructive"}>{openFile.error}</div>}
            {file && !openFile.loading && (file.binary
                ? <div className={"p-2 text-muted-foreground"}>Binary file, not shown.</div>
                : file.content === ""
                    ? <div className={"p-2 text-muted-foreground"}>Empty file.</div>
                    : <pre className={"max-h-[70vh] overflow-auto p-2 font-mono leading-5"}>{file.content}</pre>)}
        </div>
    );
};

export default DockerContainerFiles;
