import React from "react";
import { IconEye, IconEyeOff, IconPlus, IconTrash } from "@tabler/icons-react";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { EnvVarRow } from "@/features/apps/apps-validation.ts";

type Props = {
    value: EnvVarRow[];
    onChange: (rows: EnvVarRow[]) => void;
    errors: (string | null)[];
    /** variables referenced in compose.yaml, offered as quick-adds */
    suggestions?: string[];
};

const emptyRow = (): EnvVarRow => ({ name: "", value: "" });

/**
 * Edit an app's environment variables (key-value pairs).
 * They're passed to docker compose for ${VAR} interpolation and never written to the compose files.
 */
const AppEnvironmentEditor = ({ value, onChange, errors, suggestions = [] }: Props) => {
    const [showValues, setShowValues] = React.useState(false);
    const update = (index: number, patch: Partial<EnvVarRow>) =>
        onChange(value.map((r, i) => (i === index ? { ...r, ...patch } : r)));
    const remove = (index: number) => onChange(value.filter((_, i) => i !== index));
    const unused = suggestions.filter((s) => !value.some((r) => r.name.trim() === s));

    const header = (
        <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">Environment</h2>
                <p className="text-sm text-muted-foreground">
                    Variables for <code className="font-mono">${"{VAR}"}</code> in compose.yaml. Stored in the app
                    spec and passed to docker compose, never written to the compose files.
                </p>
            </div>
            <div className="flex gap-2">
                {value.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={() => setShowValues((s) => !s)}>
                        {showValues ? <IconEyeOff size={16} /> : <IconEye size={16} />}
                        {showValues ? "Hide values" : "Show values"}
                    </Button>
                )}
                <Button variant="outline" size="sm" onClick={() => onChange([...value, emptyRow()])}>
                    <IconPlus size={16} /> Add variable
                </Button>
            </div>
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            {value.length === 0 && (
                <p className="text-sm text-muted-foreground">No environment variables.</p>
            )}

            <div className="flex flex-col gap-2">
                {value.map((r, i) => (
                    <div key={i} className="flex flex-col gap-1">
                        <div className="grid gap-2 grid-cols-[1fr_auto] md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)_auto]">
                            <Input
                                className="font-mono"
                                value={r.name}
                                onChange={(e) => update(i, { name: e.target.value })}
                                placeholder="NAME"
                                aria-label="Variable name"
                                aria-invalid={!!errors[i]}
                                autoComplete="off"
                                spellCheck={false}
                            />
                            <Input
                                className="font-mono col-start-1 md:col-start-auto"
                                type={showValues ? "text" : "password"}
                                value={r.value}
                                onChange={(e) => update(i, { value: e.target.value })}
                                placeholder="value"
                                aria-label={`Value of ${r.name || "variable"}`}
                                autoComplete="off"
                                spellCheck={false}
                            />
                            <Button
                                variant="ghost"
                                size="icon"
                                className="row-start-1 col-start-2 md:row-start-auto md:col-start-auto"
                                onClick={() => remove(i)}
                                aria-label="Remove variable"
                            >
                                <IconTrash size={16} />
                            </Button>
                        </div>
                        {errors[i] && <p className="text-xs text-destructive">{errors[i]}</p>}
                    </div>
                ))}
            </div>

            {unused.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span>Used in compose.yaml:</span>
                    {unused.map((name) => (
                        <Button
                            key={name}
                            variant="outline"
                            size="sm"
                            className="font-mono"
                            onClick={() => onChange([...value, { name, value: "" }])}
                        >
                            <IconPlus size={14} /> {name}
                        </Button>
                    ))}
                </div>
            )}
        </SectionCard>
    );
};

export default AppEnvironmentEditor;
