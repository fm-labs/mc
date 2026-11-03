import React from "react";
import {Link, useSearchParams} from "react-router";
import {toast} from "react-toastify";
import {Network, RefreshCw, Search, Workflow, X} from "lucide-react";
import {Button} from "@/components/ui/button.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import {Input} from "@/components/ui/input.tsx";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select.tsx";
import {useHostsNetwork} from "@/app/containers/components/network/use-hosts-network.ts";
import {
    buildGraph,
    ContainerNode,
    Graph,
    GraphFilter,
    GraphNode,
    graphSignature,
    HostNode,
    NetworkNode,
    summarize,
} from "@/app/containers/components/network/network-graph.ts";
import {layoutGraph, LayoutMode} from "@/app/containers/components/network/network-layout.ts";
import {layoutTree} from "@/app/containers/components/network/network-tree-layout.ts";
import NetworkDiagram, {driverColor, projectColor, stateColor} from "@/app/containers/components/network/network-diagram.tsx";
import {formatAge} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

const ALL = "__all__";

const Toggle = ({checked, onChange, children}: { checked: boolean, onChange: (v: boolean) => void, children: React.ReactNode }) => (
    <button type="button" onClick={() => onChange(!checked)}
            className={`rounded-md px-2.5 py-1 text-sm transition-colors ${checked
                ? "bg-background font-medium shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
        {children}
    </button>
);

const Tile = ({label, value, hint}: { label: string, value: React.ReactNode, hint?: string }) => (
    <div className="rounded-lg border bg-card px-3 py-2" title={hint}>
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-lg font-semibold tabular-nums">{value}</div>
    </div>
);

const Row = ({label, children}: { label: string, children: React.ReactNode }) => (
    <div className="flex justify-between gap-3 py-1 text-sm">
        <span className="shrink-0 text-muted-foreground">{label}</span>
        <span className="min-w-0 text-right break-all">{children}</span>
    </div>
);

const Mono = ({children}: { children: React.ReactNode }) => <span className="font-mono text-xs">{children}</span>;

const Dot = ({color}: { color: string }) => <span className="inline-block size-2 shrink-0 rounded-full" style={{backgroundColor: color}}/>;

// ---- details panel ----

const HostDetails = ({node, graph, onSelect}: { node: HostNode, graph: Graph, onSelect: (id: string) => void }) => {
    const nets = graph.nodes.filter((n): n is NetworkNode => n.kind === "network" && n.hostId === node.hostId);
    const containers = graph.nodes.filter((n) => n.kind === "container" && n.hostId === node.hostId).length;
    const i = node.info;
    return (
        <>
            <div className="divide-y">
                {i?.ServerVersion && <Row label="Docker">{i.ServerVersion}</Row>}
                {i?.OperatingSystem && <Row label="OS">{i.OperatingSystem}</Row>}
                {i?.Architecture && <Row label="Arch">{i.Architecture}</Row>}
                <Row label="Networks">{nets.length}</Row>
                <Row label="Containers">{containers}</Row>
            </div>
            <PanelSection title="Networks">
                {nets.map((n) => (
                    <button key={n.id} type="button" onClick={() => onSelect(n.id)}
                            className="flex w-full items-center justify-between gap-2 rounded px-1.5 py-1 text-left text-sm hover:bg-muted">
                        <span className="flex min-w-0 items-center gap-2"><Dot color={driverColor(n.driver)}/><span className="truncate">{n.label}</span></span>
                        <Mono>{n.subnets[0] ?? ""}</Mono>
                    </button>
                ))}
            </PanelSection>
            <Button asChild variant="outline" size="sm" className="mt-4 w-full">
                <Link to={`/containers/${node.hostId}/networks`}>Open host networks</Link>
            </Button>
        </>
    );
};

const NetworkDetails = ({node, graph, onSelect}: { node: NetworkNode, graph: Graph, onSelect: (id: string) => void }) => {
    const members = graph.edges
        .filter((e) => e.kind === "network-container" && e.source === node.id)
        .map((e) => ({edge: e, c: graph.nodes.find((n) => n.id === e.target) as ContainerNode}))
        .filter((m) => m.c)
        .sort((a, b) => a.c.label.localeCompare(b.c.label));
    return (
        <>
            <div className="mb-2 flex flex-wrap gap-1">
                {node.builtin && <Badge variant="outline">built-in</Badge>}
                {node.internal && <Badge variant="outline" className="text-amber-600">internal</Badge>}
                {node.attachable && <Badge variant="outline">attachable</Badge>}
                {node.ipv6 && <Badge variant="outline">IPv6</Badge>}
                {node.project && <Badge variant="secondary">compose: {node.project}</Badge>}
            </div>
            <div className="divide-y">
                <Row label="Driver"><span className="inline-flex items-center gap-1.5"><Dot color={driverColor(node.driver)}/>{node.driver ?? "—"}</span></Row>
                {node.scope && <Row label="Scope">{node.scope}</Row>}
                <Row label="Subnet"><Mono>{node.subnets.join(", ") || "—"}</Mono></Row>
                <Row label="Gateway"><Mono>{node.gateways.join(", ") || "—"}</Mono></Row>
                {node.networkId && <Row label="ID"><Mono>{shortId(node.networkId)}</Mono></Row>}
            </div>
            {node.synthetic && (
                <p className="mt-2 text-xs text-muted-foreground">
                    Derived from container data. Refresh to load the full network details.
                </p>
            )}
            <PanelSection title={`Containers (${members.length})`}>
                {members.length === 0 && <p className="px-1.5 text-sm text-muted-foreground">No containers attached.</p>}
                {members.map(({edge, c}) => (
                    <button key={c.id} type="button" onClick={() => onSelect(c.id)}
                            className="flex w-full items-center justify-between gap-2 rounded px-1.5 py-1 text-left text-sm hover:bg-muted">
                        <span className="flex min-w-0 items-center gap-2"><Dot color={stateColor(c)}/><span className="truncate">{c.label}</span></span>
                        <Mono>{edge.ip ?? ""}</Mono>
                    </button>
                ))}
            </PanelSection>
        </>
    );
};

const ContainerDetails = ({node, graph, onSelect}: { node: ContainerNode, graph: Graph, onSelect: (id: string) => void }) => {
    const nets = graph.edges
        .filter((e) => e.kind === "network-container" && e.target === node.id)
        .map((e) => graph.nodes.find((n) => n.id === e.source) as NetworkNode)
        .filter(Boolean);
    const attachment = (n: NetworkNode) => node.attachments.find((a) => (a.networkId && a.networkId === n.networkId) || a.networkName === n.label);
    const shared = graph.edges
        .filter((e) => e.kind === "container-container" && (e.source === node.id || e.target === node.id))
        .map((e) => ({outgoing: e.source === node.id, other: graph.nodes.find((n) => n.id === (e.source === node.id ? e.target : e.source))!}));
    const ports = node.ports.filter((p) => p.publicPort);
    return (
        <>
            <div className="divide-y">
                <Row label="State">
                    <span className="inline-flex items-center gap-1.5"><Dot color={stateColor(node)}/>{node.state ?? "unknown"}{node.health ? ` · ${node.health}` : ""}</span>
                </Row>
                {node.image && <Row label="Image"><Mono>{node.image}</Mono></Row>}
                {node.project && (
                    <Row label="Compose">
                        <span className="inline-flex items-center gap-1.5"><Dot color={projectColor(node.project)!}/>{node.project}{node.service ? ` / ${node.service}` : ""}</span>
                    </Row>
                )}
                {node.networkMode && <Row label="Network mode"><Mono>{node.networkMode}</Mono></Row>}
                <Row label="ID"><Mono>{shortId(node.containerId)}</Mono></Row>
            </div>

            <PanelSection title={`Networks (${nets.length})`}>
                {nets.length === 0 && <p className="px-1.5 text-sm text-muted-foreground">Not attached to a visible network.</p>}
                {nets.map((n) => {
                    const a = attachment(n);
                    return (
                        <button key={n.id} type="button" onClick={() => onSelect(n.id)}
                                className="w-full rounded px-1.5 py-1 text-left text-sm hover:bg-muted">
                            <span className="flex items-center justify-between gap-2">
                                <span className="flex min-w-0 items-center gap-2"><Dot color={driverColor(n.driver)}/><span className="truncate">{n.label}</span></span>
                                <Mono>{a?.ipv4 ?? a?.ipv6 ?? ""}</Mono>
                            </span>
                            {!!a?.aliases?.length && (
                                <span className="mt-0.5 block truncate pl-4 text-xs text-muted-foreground">aliases: {a.aliases.join(", ")}</span>
                            )}
                        </button>
                    );
                })}
            </PanelSection>

            {shared.length > 0 && (
                <PanelSection title="Shared network stack">
                    {shared.map(({outgoing, other}) => (
                        <button key={other.id} type="button" onClick={() => onSelect(other.id)}
                                className="w-full rounded px-1.5 py-1 text-left text-sm hover:bg-muted">
                            {outgoing ? "uses " : "used by "}<span className="font-medium">{other.label}</span>
                        </button>
                    ))}
                </PanelSection>
            )}

            {ports.length > 0 && (
                <PanelSection title="Published ports">
                    <div className="flex flex-wrap gap-1 px-1.5">
                        {ports.map((p, i) => (
                            <Badge key={i} variant="outline" className="font-mono text-[11px]">
                                {p.ip && p.ip !== "0.0.0.0" && p.ip !== "::" ? `${p.ip}:` : ""}{p.publicPort}→{p.privatePort}/{p.type ?? "tcp"}
                            </Badge>
                        ))}
                    </div>
                </PanelSection>
            )}

            <Button asChild variant="outline" size="sm" className="mt-4 w-full">
                <Link to={`/containers/${node.hostId}/container/${node.containerId}`}>Open container</Link>
            </Button>
        </>
    );
};

const PanelSection = ({title, children}: { title: string, children: React.ReactNode }) => (
    <div className="mt-4">
        <div className="mb-1 px-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">{title}</div>
        <div className="space-y-0.5">{children}</div>
    </div>
);

const KIND_LABEL = {host: "Host", network: "Network", container: "Container"};

const DetailsPanel = ({node, graph, onSelect, onClose}: {
    node: GraphNode, graph: Graph, onSelect: (id: string) => void, onClose: () => void
}) => (
    <aside className="flex max-h-full w-80 shrink-0 flex-col overflow-hidden rounded-lg border bg-card">
        <div className="flex items-start justify-between gap-2 border-b px-4 py-3">
            <div className="min-w-0">
                <div className="text-xs text-muted-foreground">{KIND_LABEL[node.kind]} · {node.hostId}</div>
                <div className="font-mono text-sm font-semibold break-all">{node.label}</div>
            </div>
            <Button variant="ghost" size="icon" className="size-7 shrink-0" onClick={onClose} title="Close"><X/></Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
            {node.kind === "host" && <HostDetails node={node} graph={graph} onSelect={onSelect}/>}
            {node.kind === "network" && <NetworkDetails node={node} graph={graph} onSelect={onSelect}/>}
            {node.kind === "container" && <ContainerDetails node={node} graph={graph} onSelect={onSelect}/>}
        </div>
    </aside>
);

// ---- page body ----

// Docker network topology of all enabled hosts, built from data cached in this browser session
const ContainerHostsNetwork = () => {
    const {hosts, hostIds, data, missing, fetching, refresh} = useHostsNetwork();
    const [hostFilter, setHostFilter] = React.useState<string>(ALL);
    const [filter, setFilter] = React.useState<GraphFilter>({showBuiltin: true, showUnused: false, showStopped: true});
    const [search, setSearch] = React.useState("");
    const [selectedId, setSelectedId] = React.useState<string>();
    const [params, setParams] = useSearchParams();
    const mode: LayoutMode = params.get("view") === "graph" ? "graph" : "tree";
    const setMode = (m: LayoutMode) => setParams((p) => {
        if (m === "tree") p.set("view", "tree"); else p.set("view", "graph");
        return p;
    }, {replace: true});

    const visibleData = React.useMemo(
        () => (hostFilter === ALL ? data : data.filter((d) => d.hostId === hostFilter)),
        [data, hostFilter]);

    const graph = React.useMemo(() => buildGraph(visibleData, filter), [visibleData, filter]);
    const signature = graphSignature(graph);
    // only re-layout when the structure changes, not on every cache re-read
    // eslint-disable-next-line react-hooks/exhaustive-deps
    const layout = React.useMemo(() => (mode === "tree" ? layoutTree(graph) : layoutGraph(graph)), [signature, mode]);
    const summary = React.useMemo(() => summarize(graph), [graph]);
    const selected = selectedId ? graph.nodes.find((n) => n.id === selectedId) : undefined;
    const oldest = Math.min(...data.map((d) => d.cachedAt ?? Infinity));

    if (hosts.length === 0) {
        return <div className="text-sm text-muted-foreground">No container hosts configured.</div>;
    }
    if (hostIds.length === 0) {
        return (
            <div className="rounded-lg border border-dashed px-4 py-10 text-center text-sm text-muted-foreground">
                No hosts are connected. Connect a host in the sidebar to see its networks here.
            </div>
        );
    }

    const onRefresh = async () => {
        const {ok, failed} = await refresh();
        if (failed.length === 0) toast.success(`Refreshed ${ok.length} host${ok.length === 1 ? "" : "s"}`);
        else toast.error(`Failed to refresh ${failed.map((f) => f.hostId).join(", ")}`);
    };

    return (
        <div className="flex h-[calc(100svh-9rem)] min-h-[560px] flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
                <div className="inline-flex rounded-lg border bg-muted/40 p-0.5">
                    <Toggle checked={mode === "graph"} onChange={() => setMode("graph")}>
                        <span className="inline-flex items-center gap-1.5"><Network className="size-4"/>Graph</span>
                    </Toggle>
                    <Toggle checked={mode === "tree"} onChange={() => setMode("tree")}>
                        <span className="inline-flex items-center gap-1.5"><Workflow className="size-4"/>Tree</span>
                    </Toggle>
                </div>

                <Select value={hostFilter} onValueChange={(v) => { setHostFilter(v); setSelectedId(undefined); }}>
                    <SelectTrigger size="sm" className="w-44"><SelectValue/></SelectTrigger>
                    <SelectContent>
                        <SelectItem value={ALL}>All connected hosts</SelectItem>
                        {hostIds.map((id) => <SelectItem key={id} value={id}>{id}</SelectItem>)}
                    </SelectContent>
                </Select>

                <div className="inline-flex rounded-lg border bg-muted/40 p-0.5">
                    <Toggle checked={filter.showBuiltin} onChange={(v) => setFilter({...filter, showBuiltin: v})}>Built-in</Toggle>
                    <Toggle checked={filter.showUnused} onChange={(v) => setFilter({...filter, showUnused: v})}>Unused</Toggle>
                    <Toggle checked={filter.showStopped} onChange={(v) => setFilter({...filter, showStopped: v})}>Stopped</Toggle>
                </div>

                <div className="relative">
                    <Search className="pointer-events-none absolute top-1/2 left-2 size-4 -translate-y-1/2 text-muted-foreground"/>
                    <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Find name, image, IP…"
                           className="h-8 w-56 pl-8"/>
                </div>

                <div className="ml-auto flex items-center gap-3">
                    {isFinite(oldest) && (
                        <span className="text-xs text-muted-foreground" title={new Date(oldest).toLocaleString()}>
                            cached {formatAge(oldest)}
                        </span>
                    )}
                    <Button size="sm" variant="outline" onClick={onRefresh} disabled={fetching}
                            title="Fetch networks and containers of all connected hosts from the API">
                        <RefreshCw className={fetching ? "animate-spin" : ""}/> {fetching ? "Refreshing…" : "Refresh"}
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                <Tile label="Hosts" value={summary.hosts}/>
                <Tile label="Networks" value={summary.networks} hint={`${summary.customNetworks} custom`}/>
                <Tile label="Containers" value={summary.containers} hint={`${summary.running} running`}/>
                <Tile label="Running" value={summary.running}/>
                <Tile label="Multi-network" value={summary.multiHomed} hint="Containers attached to more than one network"/>
                <Tile label="Internal networks" value={summary.internal} hint="Networks without outside access"/>
            </div>

            {missing.length > 0 && (
                <p className="text-sm text-muted-foreground">
                    {fetching ? "Loading" : "No cached data for"} {missing.join(", ")}{fetching ? "…" : ". Refresh to load it."}
                </p>
            )}

            {graph.nodes.length === 0 ? (
                <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
                    {fetching ? "Loading network data…" : "No network data cached yet."}
                </div>
            ) : (
                <div className="flex min-h-0 flex-1 gap-3">
                    <NetworkDiagram graph={graph} layout={layout} selectedId={selected?.id} onSelect={setSelectedId}
                                    search={search} className="min-w-0 flex-1"/>
                    {selected && (
                        <DetailsPanel node={selected} graph={graph} onSelect={setSelectedId} onClose={() => setSelectedId(undefined)}/>
                    )}
                </div>
            )}
        </div>
    );
};

export default ContainerHostsNetwork;
