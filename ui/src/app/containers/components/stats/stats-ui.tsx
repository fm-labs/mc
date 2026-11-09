// Shared building blocks for the container stats panels.
import React from "react";
import {Link} from "react-router";
import {Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card.tsx";
import {ChartConfig} from "@/components/ui/chart.tsx";
import {Button} from "@/components/ui/button.tsx";
import {TableHead} from "@/components/ui/table.tsx";
import {ArrowDown, ArrowUp, ArrowUpDown} from "lucide-react";
import AppIcon from "@/components/app-icon.tsx";
import {DiskUsage, diskTotal} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";

export const diskConfig = {
    images: {label: "Images", color: "var(--chart-1)"},
    containers: {label: "Containers", color: "var(--chart-2)"},
    volumes: {label: "Volumes", color: "var(--chart-3)"},
    buildCache: {label: "Build cache", color: "var(--chart-4)"},
} satisfies ChartConfig;

export const diskKeys = Object.keys(diskConfig) as (keyof DiskUsage)[];

export const stateConfig = {
    running: {label: "Running", color: "var(--chart-2)"},
    paused: {label: "Paused", color: "var(--chart-4)"},
    stopped: {label: "Stopped", color: "var(--chart-1)"},
} satisfies ChartConfig;

// row height based chart height for horizontal bar charts
export const barHeight = (rows: number) => ({height: Math.max(120, rows * 36 + 60)});

// Tooltip row: color dot, series label, formatted value
export const tooltipRow = (config: ChartConfig, format: (v: number) => string) =>
    (value: unknown, name: unknown, item: { color?: string, payload?: { fill?: string } }) => (
        <div className="flex w-full items-center gap-2">
            <span className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                  style={{backgroundColor: item.color || item.payload?.fill}} />
            <span className="text-muted-foreground">{config[String(name)]?.label ?? String(name)}</span>
            <span className="ml-auto font-mono font-medium tabular-nums text-foreground">{format(Number(value))}</span>
        </div>
    );

export const StatsSection = ({title, description, action, className, children}: {
    title: React.ReactNode
    description?: React.ReactNode
    action?: React.ReactNode
    className?: string
    children: React.ReactNode
}) => (
    <Card className={className}>
        <CardHeader>
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
            {action && <CardAction>{action}</CardAction>}
        </CardHeader>
        <CardContent>{children}</CardContent>
    </Card>
);

export const EmptyNote = ({children}: { children: React.ReactNode }) => (
    <div className="py-6 text-center text-sm text-muted-foreground">{children}</div>
);

export const StatTile = ({icon, label, value, sub, tone}: {
    icon: string
    label: string
    value: React.ReactNode
    sub?: React.ReactNode
    tone?: "warn"
}) => (
    <Card className="gap-1 py-4">
        <CardHeader className="px-4">
            <CardDescription className="flex items-center gap-2">
                <AppIcon icon={icon} size={14} /> {label}
            </CardDescription>
            <CardTitle className={`text-2xl font-semibold tabular-nums ${tone === "warn" ? "text-amber-600" : ""}`}>{value}</CardTitle>
        </CardHeader>
        {sub && <CardContent className="px-4 text-xs text-muted-foreground">{sub}</CardContent>}
    </Card>
);

export const DiskBar = ({disk}: { disk: DiskUsage }) => {
    const total = diskTotal(disk);
    if (!total) return <div className="h-2 rounded-full bg-muted" />;
    return (
        <div className="flex h-2 overflow-hidden rounded-full bg-muted">
            {diskKeys.map((k) => disk[k] > 0 && (
                <div key={k} title={`${diskConfig[k].label}: ${formatBytes(disk[k])}`}
                     style={{width: `${(disk[k] / total) * 100}%`, backgroundColor: diskConfig[k].color}} />
            ))}
        </div>
    );
};

export const HostLink = ({hostId, path = ""}: { hostId: string, path?: string }) => (
    <Link to={`/containers/${hostId}${path}`} className="hover:underline">{hostId}</Link>
);

export const ContainerLink = ({hostId, containerId, name}: { hostId: string, containerId: string, name: string }) => (
    <Link to={`/containers/${hostId}/container/${containerId}`} className="font-mono hover:underline">{name}</Link>
);

// Show the first `limit` rows, with a toggle for the rest
export const useRowLimit = <T, >(rows: T[], limit = 10) => {
    const [all, setAll] = React.useState(false);
    const visible = all ? rows : rows.slice(0, limit);
    const toggle = rows.length > limit ? (
        <Button variant="ghost" size="sm" className="mt-2" onClick={() => setAll(!all)}>
            {all ? "Show less" : `Show all ${rows.length}`}
        </Button>
    ) : null;
    return {visible, toggle};
};

// Client-side sorting for the small stats tables.
// `columns` maps a column key to the value it sorts by.
export type SortDir = "asc" | "desc";
export type SortState<K extends string> = { key: K, dir: SortDir };

export const useSort = <T, K extends string>(
    rows: T[],
    columns: Record<K, (row: T) => string | number>,
    initial: SortState<NoInfer<K>>,
) => {
    const [sort, setSort] = React.useState<SortState<K>>(initial);
    const sorted = React.useMemo(() => {
        const value = columns[sort.key];
        const factor = sort.dir === "asc" ? 1 : -1;
        return [...rows].sort((a, b) => {
            const va = value(a), vb = value(b);
            const cmp = typeof va === "number" && typeof vb === "number"
                ? va - vb
                : String(va).localeCompare(String(vb), undefined, {numeric: true, sensitivity: "base"});
            return cmp * factor;
        });
    }, [rows, columns, sort]); // pass a module-level `columns` object so this stays memoized
    // Same column flips direction; a new column starts high-to-low for numbers, A-Z for text
    const toggleSort = (key: K) => setSort((s) => {
        if (s.key === key) return {key, dir: s.dir === "asc" ? "desc" : "asc"};
        const sample = rows[0] ? columns[key](rows[0]) : "";
        return {key, dir: typeof sample === "number" ? "desc" : "asc"};
    });
    return {sorted, sort, toggleSort};
};

export const SortableHead = <K extends string>({column, sort, onSort, className, children}: {
    column: NoInfer<K>
    sort: SortState<K>
    onSort: (key: K) => void
    className?: string
    children: React.ReactNode
}) => {
    const active = sort.key === column;
    const Icon = !active ? ArrowUpDown : sort.dir === "asc" ? ArrowUp : ArrowDown;
    return (
        <TableHead className={className}
                   aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}>
            <button type="button" onClick={() => onSort(column)}
                    className={`inline-flex items-center gap-1 hover:text-foreground ${className?.includes("text-right") ? "flex-row-reverse" : ""} ${active ? "text-foreground" : ""}`}>
                {children}
                <Icon className={`size-3.5 ${active ? "" : "opacity-40"}`} />
            </button>
        </TableHead>
    );
};

// Notes which hosts a panel is based on, when the needed cache is partial
export const CoverageNote = ({have, total, what}: { have: number, total: number, what: string }) =>
    have < total ? (
        <p className="text-xs text-muted-foreground">
            Based on {have} of {total} hosts. Open the {what} view of a host to cache its data.
        </p>
    ) : null;
