import React from "react";
import { IconCopy, IconFileCode, IconRefresh } from "@tabler/icons-react";
import { toast } from "sonner";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog.tsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs.tsx";
import { CompiledAppSpec } from "@/features/apps/apps.types.ts";

const errorMessage = (error: any) =>
    error?.response?.data?.detail ?? error?.message ?? String(error);

const CodeBlock = ({ children }: { children: string }) => (
    <div className="relative">
        <Button
            variant="ghost"
            size="icon"
            className="absolute top-1 right-1"
            aria-label="Copy"
            onClick={() => navigator.clipboard.writeText(children).then(() => toast.success("Copied"))}
        >
            <IconCopy size={16} />
        </Button>
        <pre className="rounded-md bg-muted px-3 py-2 pr-10 font-mono text-xs whitespace-pre overflow-auto max-h-[60vh]">
            {children}
        </pre>
    </div>
);

/**
 * Button + dialog showing the compose files an app runs with, and their merged result.
 * Loads fresh each time it opens.
 */
const CompiledSpecDialog = ({ appId, unsaved }: { appId: string; unsaved?: boolean }) => {
    const { api } = useApi();
    const [open, setOpen] = React.useState(false);
    const [data, setData] = React.useState<CompiledAppSpec | null>(null);
    const [error, setError] = React.useState<string | null>(null);
    const [loading, setLoading] = React.useState(false);

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            setData(await api.getCompiledAppSpec(appId));
        } catch (e) {
            setData(null);
            setError(errorMessage(e));
        } finally {
            setLoading(false);
        }
    }, [api, appId]);

    React.useEffect(() => {
        if (open) load();
    }, [open, load]);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline">
                    <IconFileCode size={16} /> Compiled
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-4xl">
                <DialogHeader>
                    <DialogTitle>Compiled specs</DialogTitle>
                    <DialogDescription>
                        What docker compose runs for this app: the merged result and each file, in order.
                    </DialogDescription>
                </DialogHeader>

                {unsaved && (
                    <p className="text-sm text-amber-600 dark:text-amber-400">
                        You have unsaved changes. This shows the last saved version.
                    </p>
                )}
                {error && <p className="text-sm text-destructive">Failed to load: {error}</p>}
                {!data && loading && <p className="text-sm text-muted-foreground">Loading...</p>}

                {data && (
                    <Tabs defaultValue="merged" className="min-w-0">
                        <div className="flex items-center justify-between gap-2">
                            <TabsList className="flex-wrap h-auto">
                                <TabsTrigger value="merged">Merged</TabsTrigger>
                                {data.files.map((f) => (
                                    <TabsTrigger key={f.path} value={f.path} className="font-mono text-xs">
                                        {f.name}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                            <Button variant="ghost" size="sm" onClick={load} disabled={loading}>
                                <IconRefresh size={16} /> {loading ? "Loading..." : "Reload"}
                            </Button>
                        </div>
                        <TabsContent value="merged" className="flex flex-col gap-2">
                            <p className="text-xs text-muted-foreground">
                                Output of <span className="font-mono">docker compose config</span>, with variables resolved.
                            </p>
                            {data.merged != null
                                ? <CodeBlock>{data.merged}</CodeBlock>
                                : <p className="text-sm text-destructive whitespace-pre-wrap">
                                    {data.merged_error || "No merged config."}
                                </p>}
                        </TabsContent>
                        {data.files.map((f) => (
                            <TabsContent key={f.path} value={f.path} className="flex flex-col gap-2">
                                <p className="text-xs text-muted-foreground font-mono break-all">{f.path}</p>
                                <CodeBlock>{f.content}</CodeBlock>
                            </TabsContent>
                        ))}
                    </Tabs>
                )}
            </DialogContent>
        </Dialog>
    );
};

export default CompiledSpecDialog;
