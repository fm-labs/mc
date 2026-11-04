import React from "react";
import { useLoaderData, useNavigate, useParams, useRevalidator, useSearchParams } from "react-router";
import { toast } from "sonner";
import { useApi } from "@/context/api-context.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group.tsx";
import { AppSpecDetails } from "@/features/apps/apps.types.ts";
import AppActionsPanel from "@/app/apps/components/app-actions-panel.tsx";
import CompiledSpecDialog from "@/app/apps/components/compiled-spec-dialog.tsx";
import AppVolumesEditor from "@/app/apps/components/app-volumes-editor.tsx";
import AppNetworksEditor from "@/app/apps/components/app-networks-editor.tsx";
import AppEnvironmentEditor from "@/app/apps/components/app-environment-editor.tsx";
import AppRoutingEditor from "@/app/apps/components/app-routing-editor.tsx";
import AppBundleUploadDialog, { BUNDLE_ACCEPT } from "@/app/apps/components/app-bundle-upload-dialog.tsx";
import { apiErrorMessage } from "@/features/apps/apps-errors.ts";
import {
    composeVariableRefs,
    envToRows,
    normalizeNetworks,
    routingToRows,
    rowsToEnv,
    rowsToRouting,
    validateEnvironment,
    validateRouting,
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

// new apps start from a hand-written compose.yaml or from a bundle (tar.gz)
type AppSource = "compose" | "bundle";

/**
 * Create (/manage/:hostId/apps/new, ?source=bundle) or edit (/manage/:hostId/apps/:appId) an app spec.
 */
const AppSpecEditPageView = ({hostId}: {hostId?: string}) => {
    const { appId } = useParams();
    const isNew = !appId;
    const details = (useLoaderData() as AppSpecDetails | null | undefined) ?? null;
    const { api } = useApi();
    const navigate = useNavigate();
    const revalidator = useRevalidator();
    const [searchParams] = useSearchParams();
    const [source, setSource] = React.useState<AppSource>(
        isNew && searchParams.get("source") === "bundle" ? "bundle" : "compose",
    );
    const [bundleFile, setBundleFile] = React.useState<File | null>(null);
    const fromBundle = isNew && source === "bundle";

    const initial = React.useMemo(() => ({
        id: details?.spec.id ?? "",
        title: details?.spec.title ?? "",
        description: details?.spec.description ?? "",
        stackfile: details ? (details.stackfile_content ?? "") : COMPOSE_TEMPLATE,
        volumes: details?.spec.volumes ?? [],
        networks: details?.spec.networks ?? [],
        environment: envToRows(details?.spec.environment),
        routing: routingToRows(details?.spec.routing),
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
    const envErrors = React.useMemo(() => validateEnvironment(form.environment), [form.environment]);
    const envSuggestions = React.useMemo(() => composeVariableRefs(form.stackfile), [form.stackfile]);
    const routingErrors = React.useMemo(() => validateRouting(form.routing), [form.routing]);
    const hasOverrideErrors = [...volumeErrors, ...networkErrors, ...envErrors, ...routingErrors].some(Boolean);
    const idError = isNew && form.id && !APP_ID_PATTERN.test(form.id)
        ? "Use lowercase letters, digits, '-' and '_'."
        : null;
    const canSave = fromBundle
        ? !saving && !idError && !!form.id && !!bundleFile
        : isDirty && !saving && !idError && !hasOverrideErrors && !!form.id && !!form.stackfile.trim();

    const handleSave = async () => {
        setSaving(true);
        try {
            if (fromBundle && bundleFile) {
                const created = await api.createAppFromBundle({
                    id: form.id,
                    title: form.title || null,
                    description: form.description || null,
                    bundle: bundleFile,
                });
                toast.success(`Created app ${created.spec.id} from ${bundleFile.name}`);
                created.compile_warnings?.forEach((w: string) => toast.warning(w));
                navigate(`/manage/${hostId}/apps/${encodeURIComponent(created.spec.id)}`, { replace: true });
            } else if (isNew) {
                const created = await api.createAppFromScratch({
                    id: form.id,
                    title: form.title || null,
                    description: form.description || null,
                    stackfile_content: form.stackfile,
                    volumes: normalizeVolumes(form.volumes),
                    networks: normalizeNetworks(form.networks),
                    environment: rowsToEnv(form.environment),
                    routing: rowsToRouting(form.routing),
                });
                toast.success(`Created app ${created.spec.id}`);
                created.compile_warnings?.forEach((w: string) => toast.warning(w));
                navigate(`/manage/${hostId}/apps/${encodeURIComponent(created.spec.id)}`, { replace: true });
            } else if (details) {
                const updated = await api.updateAppSpec(details.spec.id, {
                    title: form.title || null,
                    description: form.description || null,
                    stackfile_content: form.stackfile !== initial.stackfile ? form.stackfile : undefined,
                    volumes: normalizeVolumes(form.volumes),
                    networks: normalizeNetworks(form.networks),
                    environment: rowsToEnv(form.environment),
                    routing: rowsToRouting(form.routing),
                });
                toast.success(`Saved app ${details.spec.id}`);
                setCompileWarnings(updated.compile_warnings ?? []);
                revalidator.revalidate();
            }
        } catch (error) {
            toast.error(`Save failed: ${apiErrorMessage(error)}`);
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
                subtitle={details ? details.spec_path : "Create an app from a compose.yaml or a bundle."}
            >
                <div className="flex gap-2">
                    {details && <CompiledSpecDialog appId={details.spec.id} unsaved={isDirty} />}
                    <Button variant="outline" onClick={() => navigate(`/manage/${hostId}/apps`)}>Back</Button>
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

            {isNew && (
                <ToggleGroup
                    type="single"
                    variant="outline"
                    className="self-start"
                    value={source}
                    onValueChange={(v) => v && setSource(v as AppSource)}
                >
                    <ToggleGroupItem value="compose" className="px-3">Write compose.yaml</ToggleGroupItem>
                    <ToggleGroupItem value="bundle" className="px-3">Upload bundle</ToggleGroupItem>
                </ToggleGroup>
            )}

            {fromBundle ? (
                <SectionCard headerEl={
                    <div>
                        <h2 className="text-lg font-semibold">Bundle</h2>
                        <p className="text-sm text-muted-foreground">
                            A tar.gz with a compose file at its root (compose.yaml, compose.yml, docker-compose.yaml
                            or docker-compose.yml) and optional extra files. It's extracted into the app folder.
                        </p>
                    </div>
                }>
                    <div className="flex flex-col gap-2">
                        <Input
                            type="file"
                            accept={BUNDLE_ACCEPT}
                            onChange={(e) => setBundleFile(e.target.files?.[0] ?? null)}
                        />
                        <p className="text-xs text-muted-foreground">
                            Set up volumes, networks, environment and routing after the app is created.
                        </p>
                    </div>
                </SectionCard>
            ) : (
                <>
                    <SectionCard headerEl={
                        <div className="flex flex-wrap items-start justify-between gap-2">
                            <div>
                                <h2 className="text-lg font-semibold">{details?.spec.stackfile ?? "compose.yaml"}</h2>
                                {details?.stackfile_path &&
                                    <p className="text-xs text-muted-foreground font-mono mt-1">{details.stackfile_path}</p>}
                                {details && details.stackfile_content == null &&
                                    <p className="text-xs text-destructive mt-1">Compose file is missing on disk. Saving will create it.</p>}
                            </div>
                            {details && (
                                <AppBundleUploadDialog
                                    appId={details.spec.id}
                                    disabledReason={isDirty ? "Save or revert your changes first." : null}
                                    onUploaded={(updated) => {
                                        setCompileWarnings(updated.compile_warnings ?? []);
                                        revalidator.revalidate();
                                    }}
                                />
                            )}
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

                    <AppEnvironmentEditor
                        value={form.environment}
                        onChange={(environment) => setForm((f) => ({ ...f, environment }))}
                        errors={envErrors}
                        suggestions={envSuggestions}
                    />

                    <AppRoutingEditor
                        value={form.routing}
                        onChange={(routing) => setForm((f) => ({ ...f, routing }))}
                        errors={routingErrors}
                        services={details?.compose_services}
                    />
                </>
            )}

            {details && (
                <SectionCard headerEl={
                    <div>
                        <h2 className="text-lg font-semibold">Generated files</h2>
                        <p className="text-sm text-muted-foreground">
                            Generated from the volumes, networks and routes above each time you save.
                        </p>
                    </div>
                }>
                    {compileWarnings.length > 0 && (
                        <ul className="mb-3 list-disc pl-5 text-sm text-amber-600 dark:text-amber-400">
                            {compileWarnings.map((w) => <li key={w}>{w}</li>)}
                        </ul>
                    )}
                    <div className="flex flex-col gap-4">
                        {[
                            { name: "compose.override.yaml", path: details.override_path, content: details.override_content },
                            { name: "compose.traefik.yaml", path: details.traefik_override_path, content: details.traefik_override_content },
                        ].map((file) => (
                            <div key={file.name} className="flex flex-col gap-1.5">
                                <div>
                                    <h3 className="text-sm font-medium font-mono">{file.name}</h3>
                                    {file.path && <p className="text-xs text-muted-foreground font-mono">{file.path}</p>}
                                </div>
                                {file.content ? (
                                    <pre className="rounded-md bg-muted px-3 py-2 font-mono text-xs whitespace-pre-wrap break-all max-h-96 overflow-auto">
                                        {file.content}
                                    </pre>
                                ) : (
                                    <p className="text-sm text-muted-foreground">Not generated yet. Save the app to create it.</p>
                                )}
                            </div>
                        ))}
                    </div>
                </SectionCard>
            )}

            <div className="flex flex-wrap items-center gap-2">
                <Button onClick={handleSave} disabled={!canSave}>
                    {saving ? "Saving..." : (isNew ? "Create app" : "Save")}
                </Button>
                <Button variant="outline" onClick={() => setForm(initial)} disabled={!isDirty || saving || fromBundle}>
                    Revert
                </Button>
                {hasOverrideErrors && !fromBundle && (
                    <span className="text-sm text-destructive">Fix the errors above to save.</span>
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

const AppSpecEditPage = () => {
    const {hostId} = useParams<{ hostId: string }>();
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return <AppSpecEditPageView hostId={hostId} />;
};

export default AppSpecEditPage;
