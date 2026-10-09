import React from "react";
import { InfoIcon, LockIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge.tsx";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip.tsx";

// the backend masks sensitive values with this placeholder
const MASK = "*****";

type Schema = Record<string, any> | undefined;

/**
 * Render an object as a list of labelled values.
 * Labels and descriptions are taken from the JSON schema, if available.
 * Keys are listed in schema order, keys not in the schema follow.
 */
export const InventoryItemProperties = ({ data, schema }: { data: Record<string, any>, schema?: Schema }) => {
    const schemaProps: Record<string, any> = schema?.properties || {};
    const keys = [
        ...Object.keys(schemaProps).filter((key) => key in data),
        ...Object.keys(data).filter((key) => !(key in schemaProps)),
    ];

    if (keys.length === 0) {
        return <p className="text-sm text-muted-foreground">No properties.</p>;
    }

    return (
        <dl className="divide-y">
            {keys.map((key) => {
                const propSchema = schemaProps[key];
                return (
                    <div key={key} className="grid gap-1 py-2 sm:grid-cols-[minmax(10rem,1fr)_3fr] sm:gap-4">
                        <dt className="text-sm">
                            <div className="flex items-center gap-1 font-medium">
                                {propSchema?.title || key}
                                {propSchema?.description && <PropertyDescription text={propSchema.description} />}
                            </div>
                            {propSchema?.title && propSchema.title !== key &&
                                <div className="font-mono text-xs text-muted-foreground">{key}</div>}
                        </dt>
                        <dd className="min-w-0 text-sm">
                            <PropertyValue value={data[key]} schema={propSchema} />
                        </dd>
                    </div>
                );
            })}
        </dl>
    );
};


// info icon that shows the schema description on hover
const PropertyDescription = ({ text }: { text: string }) => (
    <Tooltip>
        <TooltipTrigger asChild>
            <InfoIcon size={13} className="shrink-0 cursor-help text-muted-foreground" aria-label={text} />
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">{text}</TooltipContent>
    </Tooltip>
);


const isPrimitive =(value: any) => value === null || typeof value !== "object";

const PropertyValue = ({ value, schema }: { value: any, schema?: Schema }) => {
    if (value === null || value === undefined || value === "") {
        return <span className="text-muted-foreground">–</span>;
    }
    if (value === MASK) {
        return (
            <span className="inline-flex items-center gap-1 text-muted-foreground" title="Hidden value">
                <LockIcon size={12} /> {MASK}
            </span>
        );
    }
    if (typeof value === "boolean") {
        return <Badge variant={value ? "default" : "secondary"}>{value ? "Yes" : "No"}</Badge>;
    }
    if (typeof value === "number") {
        return <span className="font-mono">{value}</span>;
    }
    if (typeof value === "string") {
        if (value.includes("\n")) {
            return <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 font-mono text-xs whitespace-pre-wrap break-words">{value}</pre>;
        }
        if (/^https?:\/\//.test(value)) {
            return <a href={value} target="_blank" rel="noreferrer" className="break-all underline">{value}</a>;
        }
        return <span className="break-words">{value}</span>;
    }
    if (Array.isArray(value)) {
        if (value.length === 0) {
            return <span className="text-muted-foreground">[]</span>;
        }
        if (value.every(isPrimitive)) {
            return (
                <div className="flex flex-wrap gap-1">
                    {value.map((v, idx) => <Badge key={idx} variant="outline">{String(v)}</Badge>)}
                </div>
            );
        }
        return (
            <div className="space-y-2">
                {value.map((v, idx) => (
                    <div key={idx} className="rounded-md border px-3">
                        {isPrimitive(v)
                            ? <div className="py-2"><PropertyValue value={v} schema={schema?.items} /></div>
                            : <InventoryItemProperties data={v} schema={schema?.items} />}
                    </div>
                ))}
            </div>
        );
    }
    if (Object.keys(value).length === 0) {
        return <span className="text-muted-foreground">{"{}"}</span>;
    }
    // nested object
    return (
        <div className="border-l-2 pl-3">
            <InventoryItemProperties data={value} schema={schema} />
        </div>
    );
};

export default InventoryItemProperties;
