import * as React from "react";
import { IconSearch } from "@tabler/icons-react";
import { Input } from "@/components/ui/input.tsx";
import { Card } from "@/components/ui/card.tsx";
import { cn } from "@/lib/utils.ts";

/**
 * Two-column layout: a list on the left (sticky on wide screens), details on the right.
 * Stacks vertically on small screens.
 */
export const ListDetailLayout = ({ list, children }: { list: React.ReactNode, children: React.ReactNode }) => (
    <div className="grid min-h-0 flex-1 gap-6 md:grid-cols-[18rem_minmax(0,1fr)] lg:grid-cols-[20rem_minmax(0,1fr)]">
        <aside className="flex min-h-0 flex-col md:sticky md:top-0 md:max-h-[calc(100svh-8rem)] md:self-start">
            {list}
        </aside>
        <section className="min-w-0">
            {children}
        </section>
    </div>
);

export type SearchableListItem = {
    id: string
    title: string
    subtitle?: string | null
    icon?: React.ReactNode
}

type SearchableListProps = {
    items: SearchableListItem[]
    selectedId?: string | null
    onSelect: (id: string) => void
    noun?: string // used in placeholder / empty text, e.g. "tools"
}

/** Searchable, selectable list of items for the left column of ListDetailLayout. */
export const SearchableList = ({ items, selectedId, onSelect, noun = "items" }: SearchableListProps) => {
    const [query, setQuery] = React.useState("");

    const filtered = React.useMemo(() => {
        const q = query.trim().toLowerCase();
        const sorted = [...items].sort((a, b) => a.title.localeCompare(b.title));
        if (!q) return sorted;
        return sorted.filter((i) =>
            i.title.toLowerCase().includes(q) || (i.subtitle || "").toLowerCase().includes(q));
    }, [items, query]);

    return (
        <div className="flex min-h-0 flex-col gap-3">
            <div className="relative">
                <IconSearch size={16} className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={`Search ${items.length} ${noun}...`}
                    className="pl-8"
                />
            </div>

            <nav className="-mx-1 flex min-h-0 flex-col gap-0.5 overflow-y-auto px-1">
                {filtered.length === 0 && (
                    <p className="px-2 py-6 text-center text-sm text-muted-foreground">
                        {items.length === 0 ? `No ${noun} available.` : `No matching ${noun}.`}
                    </p>
                )}
                {filtered.map((item) => {
                    const active = item.id === selectedId;
                    return (
                        <button
                            key={item.id}
                            type="button"
                            onClick={() => onSelect(item.id)}
                            aria-current={active ? "true" : undefined}
                            className={cn(
                                "group flex w-full items-start gap-3 rounded-md px-2.5 py-2 text-left transition-colors",
                                "hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                                active && "bg-accent",
                            )}
                        >
                            {item.icon && (
                                <span className={cn(
                                    "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border bg-background text-muted-foreground",
                                    active && "border-primary/40 text-primary",
                                )}>
                                    {item.icon}
                                </span>
                            )}
                            <span className="min-w-0 flex-1">
                                <span className={cn("block truncate text-sm font-medium", active && "text-primary")}>
                                    {item.title}
                                </span>
                                <span className="block truncate text-xs text-muted-foreground">
                                    {item.subtitle || "No description"}
                                </span>
                            </span>
                        </button>
                    );
                })}
            </nav>
        </div>
    );
};

/** Placeholder for the right column when nothing is selected. */
export const DetailEmpty = ({ icon, children }: { icon?: React.ReactNode, children: React.ReactNode }) => (
    <Card className="flex h-full min-h-64 items-center justify-center border-dashed">
        <div className="flex flex-col items-center gap-2 text-center text-muted-foreground">
            {icon}
            <p className="text-sm">{children}</p>
        </div>
    </Card>
);
