import React from "react";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Label } from "@/components/ui/label.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.tsx";
import { AppRoutingMode } from "@/features/apps/apps.types.ts";
import { RouteRow } from "@/features/apps/apps-validation.ts";

type Props = {
    value: RouteRow[];
    onChange: (rows: RouteRow[]) => void;
    errors: (string | null)[];
    /** service name -> container ports, from the saved compose.yaml */
    services?: Record<string, number[]>;
};

const MODES: { value: AppRoutingMode; label: string }[] = [
    { value: "http", label: "HTTP" },
    { value: "https", label: "HTTPS" },
    { value: "http+https", label: "HTTP + HTTPS" },
];

/**
 * Edit an app's routes: which service port traefik serves on which domains.
 * Compiled into compose.traefik.yaml on save.
 */
const AppRoutingEditor = ({ value, onChange, errors, services = {} }: Props) => {
    const id = React.useId();
    const serviceNames = Object.keys(services);
    const update = (index: number, patch: Partial<RouteRow>) =>
        onChange(value.map((r, i) => (i === index ? { ...r, ...patch } : r)));
    const remove = (index: number) => onChange(value.filter((_, i) => i !== index));

    const addRoute = () => {
        // prefill when compose.yaml leaves only one sensible choice
        const service = serviceNames.length === 1 ? serviceNames[0] : "";
        const ports = services[service] ?? [];
        onChange([...value, {
            service_name: service,
            container_port: ports.length > 0 ? String(ports[0]) : "",
            mode: "https",
            domains: "",
        }]);
    };

    const header = (
        <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">Routing</h2>
                <p className="text-sm text-muted-foreground">
                    Serve a service port on one or more domains through traefik. HTTPS uses a Let's Encrypt
                    certificate. Routed services join the traefik network.
                </p>
            </div>
            <Button variant="outline" size="sm" onClick={addRoute}>
                <IconPlus size={16} /> Add route
            </Button>
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            <datalist id={`${id}-services`}>
                {serviceNames.map((s) => <option key={s} value={s} />)}
            </datalist>

            {value.length === 0 && <p className="text-sm text-muted-foreground">No routes.</p>}

            <div className="flex flex-col gap-3">
                {value.map((r, i) => {
                    const ports = services[r.service_name.trim()] ?? [];
                    const portsListId = `${id}-ports-${i}`;
                    return (
                        <div key={i} className="flex flex-col gap-2 rounded-md border p-3">
                            <datalist id={portsListId}>
                                {ports.map((p) => <option key={p} value={p} />)}
                            </datalist>
                            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_7rem_10rem_auto] md:items-end">
                                <div className="flex flex-col gap-1.5">
                                    <Label htmlFor={`route-service-${i}`}>Service</Label>
                                    <Input
                                        id={`route-service-${i}`}
                                        className="font-mono"
                                        list={`${id}-services`}
                                        value={r.service_name}
                                        onChange={(e) => update(i, { service_name: e.target.value })}
                                        placeholder="app"
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="flex flex-col gap-1.5">
                                    <Label htmlFor={`route-port-${i}`}>Port</Label>
                                    <Input
                                        id={`route-port-${i}`}
                                        className="font-mono"
                                        inputMode="numeric"
                                        list={portsListId}
                                        value={r.container_port}
                                        onChange={(e) => update(i, { container_port: e.target.value })}
                                        placeholder="80"
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="flex flex-col gap-1.5">
                                    <Label htmlFor={`route-mode-${i}`}>Protocol</Label>
                                    <Select value={r.mode} onValueChange={(mode) => update(i, { mode: mode as AppRoutingMode })}>
                                        <SelectTrigger id={`route-mode-${i}`} className="w-full">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {MODES.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button variant="ghost" size="icon" onClick={() => remove(i)} aria-label="Remove route">
                                    <IconTrash size={16} />
                                </Button>
                            </div>
                            <div className="flex flex-col gap-1.5">
                                <Label htmlFor={`route-domains-${i}`}>Domains</Label>
                                <Input
                                    id={`route-domains-${i}`}
                                    className="font-mono"
                                    value={r.domains}
                                    onChange={(e) => update(i, { domains: e.target.value })}
                                    placeholder="app.example.com, www.example.com"
                                    autoComplete="off"
                                    spellCheck={false}
                                />
                            </div>
                            {errors[i] && <p className="text-xs text-destructive">{errors[i]}</p>}
                        </div>
                    );
                })}
            </div>
        </SectionCard>
    );
};

export default AppRoutingEditor;
