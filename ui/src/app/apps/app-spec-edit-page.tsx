import React from "react";
import { useLoaderData, useNavigate, useParams, useRevalidator } from "react-router";
import { toast } from "sonner";
import { useApi } from "@/context/api-context.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import { AppSpecDetails } from "@/features/apps/apps.types.ts";
import AppActionsPanel from "@/app/apps/components/app-actions-panel.tsx";
import CompiledSpecDialog from "@/app/apps/components/compiled-spec-dialog.tsx";
import AppVolumesEditor from "@/app/apps/components/app-volumes-editor.tsx";
import AppNetworksEditor from "@/app/apps/components/app-networks-editor.tsx";
import {
    normalizeNetworks,
    normalizeVolumes,
    validateNetworks,
    validateVolumes,
} from "@/features/apps/apps-validation.ts";

const COMPOSE_TEMPLATE = `services:
  app:
    image: nginx:alpine
    restart: unless-stopped
`;

const APP_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,62}$/;

const errorMessage = (error: any) => {
    const detail = error?.response?.data?.detail;
    // FastAPI validation errors: [{loc: ["body", "volumes", 0, "container_path"], msg: "..."}]
    if (Array.isArray(detail)) {
        return detail.map((d: any) => {
            const loc = (d.loc || []).filter((part: any) => part !== "body").join(".");
            return loc ? `${loc}: ${d.msg}` : d.msg;
        }).join("; ");
    }
    return detail ?? error?.message ?? String(error);
};

/**
 * Create (/admin/apps/new) or edit (/admin/apps/:appId) an app spec with a hand-written compose.yaml.
 */
const AppSpecEditPage = () => {
    const { appId } = useParams();
    const isNew = !appId;
    const details = (useLoaderData() as AppSpecDetails | null | undefined) ?? null;
    const { api } = useApi();
    const navigate = useNavigate();
    const revalidator = useRevalidator();

    const initial = React.useMemo(() => ({
        id: details?.spec.id ?? "",
        title: details?.spec.title ?? "",
        description: details?.spec.description ?? "",
        stackfile: details ? (details.stackfile_content ?? "") : COMPOSE_TEMPLATE,
        volumes: details?.spec.volumes ?? [],
        networks: details?.spec.networks ?? [],
    }), [details]);

    const [form, setForm] = React.useState(initial);
    const [saving, setSaving] = React.useState(false);
    // warnings from the last save's override generation
    const [compileWarnings, setCompileWarnings] = React.useState<string[]>([]);
    React.useEffect(() => setForm(initial), [initial]);

    type TextField = "id" | "title" | "description" | "stackfile";
    const set = (key: TextField) =>
        (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
            setForm((f) => ({ ...f, [key]: e.target.value }));

    const isDirty = JSON.stringify(form) !== JSON.stringify(initial);
    const volumeErrors = React.useMemo(() => validateVolumes(form.volumes), [form.volumes]);
    const networkErrors = React.useMemo(() => validateNetworks(form.networks), [form.networks]);
    const hasOverrideErrors = [...volumeErrors, ...networkErrors].some(Boolean);
    const idError = isNew && form.id && !APP_ID_PATTERN.test(form.id)
        ? "Use lowercase letters, digits, '-' and '_'."
        : null;
    const canSave = isDirty && !saving && !idError && !hasOverrideErrors && !!form.id && !!form.stackfile.trim();

    const handleSave = async () => {
        setSaving(true);
        try {
            if (isNew) {
                const created = await api.createAppFromScratch({
                    id: form.id,
                    title: form.title || null,
                    description: form.description || null,
                    stackfile_content: form.stackfile,
                    volumes: normalizeVolumes(form.volumes),
                    networks: normalizeNetworks(form.networks),
                });
                toast.success(`Created app ${created.spec.id}`);
                created.compile_warnings?.forEach((w: string) => toast.warning(w));
                navigate(`/admin/apps/${encodeURIComponent(created.spec.id)}`, { replace: true });
            } else if (details) {
                const updated = await api.updateAppSpec(details.spec.id, {
                    title: form.title || null,
                    description: form.description || null,
                    stackfile_content: form.stackfile !== initial.stackfile ? form.stackfile : undefined,
                    volumes: normalizeVolumes(form.volumes),
                    networks: normalizeNetworks(form.networks),
                });
                toast.success(`Saved app ${details.spec.id}`);
                setCompileWarnings(updated.compile_warnings ?? []);
                revalidator.revalidate();
            }
        } catch (error) {
            toast.error(`Save failed: ${errorMessage(error)}`);
        } finally {
            setSaving(false);
        }
    };

    if (!isNew && !details) {
        return <MainContent><p className="text-sm text-destructive">App not found.</p></MainContent>;
    }

    return (
        <MainContent>
            <Header
                title={details ? (details.spec.title || details.spec.id) : "New app"}
                subtitle={details ? details.spec_path : "Create an app from a hand-written compose.yaml."}
            >
                <div className="flex gap-2">
                    {details && <CompiledSpecDialog appId={details.spec.id} unsaved={isDirty} />}
                    <Button variant="outline" onClick={() => navigate("/admin/apps")}>Back</Button>
                </div>
            </Header>

            <SectionCard title="App">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="flex flex-col gap-2">
                        <Label htmlFor="app-id">Id</Label>
                        <Input
                            id="app-id"
                            className="font-mono"
                            value={form.id}
                            onChange={set("id")}
                            readOnly={!isNew}
                            placeholder="my-app"
                            aria-invalid={!!idError}
                        />
                        {idError
                            ? <p className="text-xs text-destructive">{idError}</p>
                            : <p className="text-xs text-muted-foreground">Also used as the compose project name. Can't be changed later.</p>}
                    </div>
                    <div className="flex flex-col gap-2">
                        <Label htmlFor="app-title">Title</Label>
                        <Input id="app-title" value={form.title} onChange={set("title")} placeholder="My App" />
                    </div>
                    <div className="flex flex-col gap-2 md:col-span-2">
                        <Label htmlFor="app-description">Description</Label>
                        <Input id="app-description" value={form.description} onChange={set("description")} />
                    </div>
                </div>
            </SectionCard>

            <SectionCard headerEl={
                <div>
                    <h2 className="text-lg font-semibold">compose.yaml</h2>
                    {details?.stackfile_path &&
                        <p className="text-xs text-muted-foreground font-mono mt-1">{details.stackfile_path}</p>}
                    {details && details.stackfile_content == null &&
                        <p className="text-xs text-destructive mt-1">Compose file is missing on disk. Saving will create it.</p>}
                </div>
            }>
                <Textarea
                    className="font-mono text-xs min-h-96 max-h-[70vh] overflow-auto"
                    value={form.stackfile}
                    onChange={set("stackfile")}
                    spellCheck={false}
                />
            </SectionCard>

            <AppVolumesEditor
                value={form.volumes}
                onChange={(volumes) => setForm((f) => ({ ...f, volumes }))}
                errors={volumeErrors}
                suggestions={details?.compose_volumes}
            />

            <AppNetworksEditor
                value={form.networks}
                onChange={(networks) => setForm((f) => ({ ...f, networks }))}
                errors={networkErrors}
                suggestions={details?.compose_networks}
            />

            {details && (
                <SectionCard headerEl={
                    <div>
                        <h2 className="text-lg font-semibold">compose.override.yaml</h2>
                        <p className="text-sm text-muted-foreground">
                            Generated from the volumes and networks above each time you save.
                        </p>
                        {details.override_path &&
                            <p className="text-xs text-muted-foreground font-mono mt-1">{details.override_path}</p>}
                    </div>
                }>
                    {compileWarnings.length > 0 && (
                        <ul className="mb-3 list-disc pl-5 text-sm text-amber-600 dark:text-amber-400">
                            {compileWarnings.map((w) => <li key={w}>{w}</li>)}
                        </ul>
                    )}
                    {details.override_content ? (
                        <pre className="rounded-md bg-muted px-3 py-2 font-mono text-xs whitespace-pre-wrap break-all max-h-96 overflow-auto">
                            {details.override_content}
                        </pre>
                    ) : (
                        <p className="text-sm text-muted-foreground">Not generated yet. Save the app to create it.</p>
                    )}
                </SectionCard>
            )}

            <div className="flex flex-wrap items-center gap-2">
                <Button onClick={handleSave} disabled={!canSave}>
                    {saving ? "Saving..." : (isNew ? "Create app" : "Save")}
                </Button>
                <Button variant="outline" onClick={() => setForm(initial)} disabled={!isDirty || saving}>
                    Revert
                </Button>
                {hasOverrideErrors && (
                    <span className="text-sm text-destructive">Fix the volume and network errors above to save.</span>
                )}
            </div>

            {details && (
                <AppActionsPanel
                    appId={details.spec.id}
                    disabledReason={isDirty ? "Save or revert your changes before running the app." : null}
                />
            )}
        </MainContent>
    );
};

export default AppSpecEditPage;
