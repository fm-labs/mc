import React from "react";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Checkbox } from "@/components/ui/checkbox.tsx";
import { AppVolumeSpec } from "@/features/apps/apps.types.ts";

type Props = {
    value: AppVolumeSpec[];
    onChange: (volumes: AppVolumeSpec[]) => void;
    errors: (string | null)[];
    /** volume names declared in compose.yaml, offered as suggestions */
    suggestions?: string[];
};

const emptyVolume = (): AppVolumeSpec => ({ volume_name: "", container_path: "", bind: false, host_path: null });

/**
 * Edit the volume overrides of an app spec (AppVolumeSpec list).
 */
const AppVolumesEditor = ({ value, onChange, errors, suggestions = [] }: Props) => {
    const listId = React.useId();
    const update = (index: number, patch: Partial<AppVolumeSpec>) =>
        onChange(value.map((v, i) => (i === index ? { ...v, ...patch } : v)));
    const remove = (index: number) => onChange(value.filter((_, i) => i !== index));
    const unused = suggestions.filter((s) => !value.some((v) => v.volume_name === s));

    const header = (
        <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">Volumes</h2>
                <p className="text-sm text-muted-foreground">
                    Override where volumes are stored. Use a named volume, or bind-mount a host path.
                </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => onChange([...value, emptyVolume()])}>
                <IconPlus size={16} /> Add volume
            </Button>
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            <datalist id={listId}>
                {suggestions.map((s) => <option key={s} value={s} />)}
            </datalist>

            {value.length === 0 && (
                <p className="text-sm text-muted-foreground">No volume overrides.</p>
            )}

            <div className="flex flex-col gap-3">
                {value.map((v, i) => (
                    <div key={i} className="flex flex-col gap-2 rounded-md border p-3">
                        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto_1fr_auto] md:items-end">
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor={`vol-name-${i}`}>Volume</Label>
                                <Input
                                    id={`vol-name-${i}`}
                                    className="font-mono"
                                    list={listId}
                                    value={v.volume_name}
                                    onChange={(e) => update(i, { volume_name: e.target.value })}
                                    placeholder="data"
                                />
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor={`vol-path-${i}`}>Container path</Label>
                                <Input
                                    id={`vol-path-${i}`}
                                    className="font-mono"
                                    value={v.container_path}
                                    onChange={(e) => update(i, { container_path: e.target.value })}
                                    placeholder="/data"
                                />
                            </div>
                            <div className="flex h-9 items-center gap-2">
                                <Checkbox
                                    id={`vol-bind-${i}`}
                                    checked={!!v.bind}
                                    onCheckedChange={(checked) => update(i, { bind: checked === true })}
                                />
                                <Label htmlFor={`vol-bind-${i}`}>Bind mount</Label>
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor={`vol-host-${i}`}>Host path</Label>
                                <Input
                                    id={`vol-host-${i}`}
                                    className="font-mono"
                                    value={v.bind ? (v.host_path ?? "") : ""}
                                    onChange={(e) => update(i, { host_path: e.target.value })}
                                    disabled={!v.bind}
                                    placeholder={v.bind ? "./data or /srv/data" : "named volume"}
                                />
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => remove(i)} aria-label="Remove volume">
                                <IconTrash size={16} />
                            </Button>
                        </div>
                        {errors[i] && <p className="text-xs text-destructive">{errors[i]}</p>}
                    </div>
                ))}
            </div>

            {unused.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span>Declared in compose.yaml:</span>
                    {unused.map((name) => (
                        <Button
                            key={name}
                            variant="outline"
                            size="sm"
                            className="font-mono"
                            onClick={() => onChange([...value, { ...emptyVolume(), volume_name: name }])}
                        >
                            <IconPlus size={14} /> {name}
                        </Button>
                    ))}
                </div>
            )}
        </SectionCard>
    );
};

export default AppVolumesEditor;
