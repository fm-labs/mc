import React from "react";
import { toast } from "sonner";
import { useApi } from "@/context/api-context.tsx";
import SectionCard from "@/components/section-card.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Badge } from "@/components/ui/badge.tsx";

type ConfigFile = {
    conf: string;
    path: string;
    format: "json" | "text";
    exists: boolean;
    writable: boolean;
    content: string;
};

const errorMessage = (error: any) =>
    error?.response?.data?.detail ?? error?.message ?? String(error);

const ConfigFileEditor = ({ conf, title, description }: { conf: string; title: string; description?: string }) => {
    const { api } = useApi();
    const [config, setConfig] = React.useState<ConfigFile | null>(null);
    const [content, setContent] = React.useState("");
    const [loadError, setLoadError] = React.useState<string | null>(null);
    const [saving, setSaving] = React.useState(false);

    const load = React.useCallback(async () => {
        setLoadError(null);
        try {
            const data: ConfigFile = await api.get(`/api/config`, { params: { conf } });
            setConfig(data);
            setContent(data.content);
        } catch (error) {
            setLoadError(errorMessage(error));
        }
    }, [api, conf]);

    React.useEffect(() => {
        load();
    }, [load]);

    const isDirty = config !== null && content !== config.content;

    const jsonError = React.useMemo(() => {
        if (config?.format !== "json" || !content.trim()) return null;
        try {
            JSON.parse(content);
            return null;
        } catch (e: any) {
            return e.message as string;
        }
    }, [config?.format, content]);

    const handleSave = async () => {
        setSaving(true);
        try {
            const data: ConfigFile = await api.post(`/api/config`, { content }, { params: { conf } });
            setConfig(data);
            setContent(data.content);
            toast.success(`Saved ${data.path}`);
        } catch (error) {
            toast.error(`Save failed: ${errorMessage(error)}`);
        } finally {
            setSaving(false);
        }
    };

    const header = (
        <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">{title}</h2>
                {description && <p className="text-sm text-muted-foreground">{description}</p>}
                {config && <p className="text-xs text-muted-foreground font-mono mt-1">{config.path}</p>}
            </div>
            {config && (
                <div className="flex gap-2">
                    {!config.exists && <Badge variant="outline">Not created yet</Badge>}
                    <Badge variant={config.writable ? "secondary" : "outline"}>
                        {config.writable ? "Editable" : "Read-only"}
                    </Badge>
                </div>
            )}
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            {loadError && <p className="text-sm text-destructive">Failed to load: {loadError}</p>}
            {config && (
                <div className="flex flex-col gap-3">
                    <Textarea
                        className="font-mono text-xs min-h-64 max-h-[60vh] overflow-auto"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        readOnly={!config.writable}
                        spellCheck={false}
                        aria-invalid={!!jsonError}
                    />
                    {jsonError && <p className="text-sm text-destructive">Invalid JSON: {jsonError}</p>}
                    {config.writable ? (
                        <div className="flex gap-2">
                            <Button onClick={handleSave} disabled={!isDirty || saving || !!jsonError}>
                                {saving ? "Saving..." : "Save"}
                            </Button>
                            <Button variant="outline" onClick={() => setContent(config.content)} disabled={!isDirty || saving}>
                                Revert
                            </Button>
                        </div>
                    ) : (
                        <p className="text-xs text-muted-foreground">
                            Editing is disabled on the server for this file.
                        </p>
                    )}
                </div>
            )}
        </SectionCard>
    );
};

export default ConfigFileEditor;
