// Small display helpers shared by the docker host views
import React from 'react';
import ReactJson from "@microlink/react-json-view";
import {Check, Copy, Minus} from "lucide-react";
import {toast} from "react-toastify";
import {Badge} from "@/components/ui/badge.tsx";
import {Button} from "@/components/ui/button.tsx";
import {useTheme} from "@/context/theme-provider.tsx";

export type Row = [label: string, value: React.ReactNode]

const isEmpty = (v: unknown) =>
    v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);

export const Bool = ({value}: { value?: boolean }) => value === undefined ? null : value
    ? <span className="inline-flex items-center gap-1 text-green-600"><Check className="size-3.5"/>Yes</span>
    : <span className="inline-flex items-center gap-1 text-muted-foreground"><Minus className="size-3.5"/>No</span>;

export const Mono = ({children}: { children: React.ReactNode }) =>
    <span className="font-mono text-xs break-all">{children}</span>;

export const BadgeList = ({items}: { items?: (string | null | undefined)[] | null }) => {
    const list = (items ?? []).filter(Boolean) as string[];
    if (list.length === 0) return null;
    return (
        <div className="flex flex-wrap justify-end gap-1">
            {list.map((i) => <Badge key={i} variant="secondary" className="font-mono">{i}</Badge>)}
        </div>
    );
};

// Label / value list; rows with empty values are skipped
export const PropList = ({rows}: { rows: Row[] }) => {
    const visible = rows.filter(([, v]) => !isEmpty(v));
    if (visible.length === 0) return <p className="text-sm text-muted-foreground">No data.</p>;
    return (
        <dl className="divide-y text-sm">
            {visible.map(([label, value]) => (
                <div key={label} className="flex items-start justify-between gap-4 py-1.5">
                    <dt className="shrink-0 text-muted-foreground">{label}</dt>
                    <dd className="min-w-0 text-right font-medium">{value}</dd>
                </div>
            ))}
        </dl>
    );
};

export const Section = ({title, children}: { title: string, children: React.ReactNode }) => (
    <section className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</h4>
        {children}
    </section>
);

// key=value list (env vars, labels)
export const KeyValues = ({entries}: { entries: [string, string][] }) => {
    if (entries.length === 0) return <p className="text-sm text-muted-foreground">None.</p>;
    return (
        <div className="divide-y rounded-md border font-mono text-xs">
            {entries.map(([k, v], i) => (
                <div key={`${k}-${i}`} className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3 px-3 py-1.5">
                    <span className="break-all text-muted-foreground">{k}</span>
                    <span className="break-all">{v}</span>
                </div>
            ))}
        </div>
    );
};

export const useIsDark = () => {
    const {theme} = useTheme();
    if (theme === "system") {
        return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return theme === "dark";
};

export const RawJson = ({data, name}: { data: any, name: string }) => {
    const isDark = useIsDark();
    const copy = async () => {
        try {
            await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            toast.success(`Copied ${name} JSON`);
        } catch {
            toast.error("Could not copy to clipboard");
        }
    };
    if (!data) return <p className="text-sm text-muted-foreground">Not loaded yet.</p>;
    return (
        <div className="relative">
            <Button variant="outline" size="sm" className="absolute right-2 top-2 z-10" onClick={copy}>
                <Copy/> Copy
            </Button>
            <div className="max-h-[600px] overflow-auto rounded-md border p-3 text-xs">
                <ReactJson
                    src={data}
                    name={false}
                    collapsed={1}
                    theme={isDark ? "ocean" : "rjv-default"}
                    style={{backgroundColor: "transparent"}}
                    enableClipboard={true}
                    displayObjectSize={true}
                    displayDataTypes={false}
                    sortKeys={true}/>
            </div>
        </div>
    );
};
