import React from "react";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Checkbox } from "@/components/ui/checkbox.tsx";
import { AppNetworkSpec } from "@/features/apps/apps.types.ts";

type Props = {
    value: AppNetworkSpec[];
    onChange: (networks: AppNetworkSpec[]) => void;
    errors: (string | null)[];
    /** network names declared in compose.yaml, offered as suggestions */
    suggestions?: string[];
};

const emptyNetwork = (): AppNetworkSpec => ({ network_name: "", external: false });

/**
 * Edit the network overrides of an app spec (AppNetworkSpec list).
 */
const AppNetworksEditor = ({ value, onChange, errors, suggestions = [] }: Props) => {
    const listId = React.useId();
    const update = (index: number, patch: Partial<AppNetworkSpec>) =>
        onChange(value.map((n, i) => (i === index ? { ...n, ...patch } : n)));
    const remove = (index: number) => onChange(value.filter((_, i) => i !== index));
    const unused = suggestions.filter((s) => !value.some((n) => n.network_name === s));

    const header = (
        <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">Networks</h2>
                <p className="text-sm text-muted-foreground">
                    Networks the app joins. External networks must already exist on the Docker host.
                </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => onChange([...value, emptyNetwork()])}>
                <IconPlus size={16} /> Add network
            </Button>
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            <datalist id={listId}>
                {suggestions.map((s) => <option key={s} value={s} />)}
            </datalist>

            {value.length === 0 && (
                <p className="text-sm text-muted-foreground">No network overrides.</p>
            )}

            <div className="flex flex-col gap-3">
                {value.map((n, i) => (
                    <div key={i} className="flex flex-col gap-2 rounded-md border p-3">
                        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto] md:items-end">
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor={`net-name-${i}`}>Network</Label>
                                <Input
                                    id={`net-name-${i}`}
                                    className="font-mono"
                                    list={listId}
                                    value={n.network_name}
                                    onChange={(e) => update(i, { network_name: e.target.value })}
                                    placeholder="proxy"
                                />
                            </div>
                            <div className="flex h-9 items-center gap-2">
                                <Checkbox
                                    id={`net-external-${i}`}
                                    checked={!!n.external}
                                    onCheckedChange={(checked) => update(i, { external: checked === true })}
                                />
                                <Label htmlFor={`net-external-${i}`}>External</Label>
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => remove(i)} aria-label="Remove network">
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
                            onClick={() => onChange([...value, { ...emptyNetwork(), network_name: name }])}
                        >
                            <IconPlus size={14} /> {name}
                        </Button>
                    ))}
                </div>
            )}
        </SectionCard>
    );
};

export default AppNetworksEditor;
