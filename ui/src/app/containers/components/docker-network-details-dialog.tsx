import React from "react";
import {Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle} from "@/components/ui/dialog.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Badge} from "@/components/ui/badge.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {Bool, KeyValues, Mono, PropList, RawJson, Section} from "@/app/containers/components/docker-ui.tsx";
import {ContainerLink} from "@/app/containers/components/stats/stats-ui.tsx";
import {formatAge} from "@/app/containers/components/stats/format.ts";
import {shortId} from "@/app/containers/components/stats/host-stats.ts";

export type NetworkEndpoint = {
    id: string
    name: string
    state?: string
    ipv4?: string
    ipv6?: string
    mac?: string
}

// Networks that ship with docker and can't be removed
export const BUILTIN_NETWORKS = ["bridge", "host", "none"];
export const isBuiltinNetwork = (n: any) => BUILTIN_NETWORKS.includes(n?.Name);

const stripCidr = (ip?: string) => ip ? ip.replace(/\/\d+$/, "") : undefined;

// network id -> connected containers.
// Uses the container list from `docker system df`, plus the network's own `Containers` field when present
// (the list endpoint usually leaves it empty).
export const useNetworkEndpoints = (networks?: any[]) => {
    const {summary} = useContainerHost();
    return React.useMemo(() => {
        const m: Record<string, NetworkEndpoint[]> = {};
        const add = (netId: string, ep: NetworkEndpoint) => {
            const list = (m[netId] ??= []);
            if (!list.some((e) => e.id === ep.id)) list.push(ep);
        };
        const byName: Record<string, string> = {};
        (networks ?? []).forEach((n) => { byName[n.Name] = n.Id; });

        ((summary?.Containers ?? []) as any[]).forEach((c) => {
            const name = (c.Names?.[0] ?? shortId(c.Id)).replace(/^\//, "");
            Object.entries(c.NetworkSettings?.Networks ?? {}).forEach(([netName, s]: [string, any]) => {
                const netId = s?.NetworkID || byName[netName];
                if (!netId) return;
                add(netId, {
                    id: c.Id, name, state: c.State,
                    ipv4: s?.IPAddress || undefined,
                    ipv6: s?.GlobalIPv6Address || undefined,
                    mac: s?.MacAddress || undefined,
                });
            });
        });
        (networks ?? []).forEach((n) => {
            Object.entries(n.Containers ?? {}).forEach(([cid, c]: [string, any]) => {
                add(n.Id, {
                    id: cid, name: c?.Name ?? shortId(cid),
                    ipv4: stripCidr(c?.IPv4Address), ipv6: stripCidr(c?.IPv6Address), mac: c?.MacAddress || undefined,
                });
            });
        });
        return m;
    }, [summary, networks]);
};

export const networkSubnets = (n: any): string[] =>
    ((n?.IPAM?.Config ?? []) as any[]).map((c) => c?.Subnet).filter(Boolean);

const DockerNetworkDetailsDialog = ({network, endpoints, open, onOpenChange}: {
    network?: any
    endpoints: NetworkEndpoint[]
    open: boolean
    onOpenChange: (open: boolean) => void
}) => {
    const {config: hostConfig} = useContainerHost();
    if (!network) return null;

    const labels = Object.entries(network.Labels ?? {}) as [string, string][];
    const options = Object.entries(network.Options ?? {}) as [string, string][];
    const ipam: any[] = network.IPAM?.Config ?? [];
    const created = network.Created ? new Date(network.Created) : undefined;
    const builtin = isBuiltinNetwork(network);
    const project = network.Labels?.["com.docker.compose.project"];

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="flex max-h-[90vh] flex-col gap-4 sm:max-w-3xl">
                <DialogHeader className="text-left">
                    <div className="flex items-start gap-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-muted">
                            <AppIcon icon="container-network" size={22}/>
                        </div>
                        <div className="min-w-0">
                            <DialogTitle className="break-all font-mono text-base">{network.Name}</DialogTitle>
                            <DialogDescription className="mt-1 flex flex-wrap items-center gap-2">
                                <Mono>{shortId(network.Id)}</Mono>
                                {endpoints.length > 0
                                    ? <Badge className="bg-green-600/15 text-green-700 dark:text-green-400">in use · {endpoints.length}</Badge>
                                    : <Badge variant="outline">unused</Badge>}
                                {builtin && <Badge variant="outline">built-in</Badge>}
                                {network.Internal && <Badge variant="outline" className="text-amber-600">internal</Badge>}
                                {project && <Badge variant="secondary">compose: {project}</Badge>}
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <div className="grid grid-cols-2 gap-3 rounded-lg border bg-muted/30 px-4 py-3 text-sm sm:grid-cols-4">
                    <div><div className="text-xs text-muted-foreground">Driver</div><div className="font-semibold">{network.Driver ?? "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Scope</div><div className="font-semibold">{network.Scope ?? "—"}</div></div>
                    <div><div className="text-xs text-muted-foreground">Subnet</div><div className="font-mono text-xs font-semibold break-all">{networkSubnets(network).join(", ") || "—"}</div></div>
                    <div title={created?.toLocaleString()}><div className="text-xs text-muted-foreground">Created</div><div className="font-semibold">{created ? formatAge(created.getTime()) : "—"}</div></div>
                </div>

                <Tabs defaultValue="overview" className="min-h-0 flex-1">
                    <TabsList>
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="ipam">IPAM</TabsTrigger>
                        <TabsTrigger value="labels">Labels ({labels.length})</TabsTrigger>
                        <TabsTrigger value="options">Options ({options.length})</TabsTrigger>
                        <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                    </TabsList>

                    <div className="mt-2 h-[min(28rem,55vh)] overflow-y-auto pr-1">
                        <TabsContent value="overview" className="space-y-5">
                            <Section title={`Connected containers (${endpoints.length})`}>
                                {endpoints.length > 0 ? (
                                    <div className="overflow-x-auto rounded-md border">
                                        <table className="w-full text-sm">
                                            <thead className="bg-muted/40 text-xs text-muted-foreground">
                                            <tr>
                                                <th className="px-3 py-1.5 text-left font-medium">Container</th>
                                                <th className="px-3 py-1.5 text-left font-medium">IPv4</th>
                                                <th className="px-3 py-1.5 text-left font-medium">IPv6</th>
                                                <th className="px-3 py-1.5 text-left font-medium">MAC</th>
                                                <th className="px-3 py-1.5 text-right font-medium">State</th>
                                            </tr>
                                            </thead>
                                            <tbody className="divide-y">
                                            {endpoints.map((e) => (
                                                <tr key={e.id}>
                                                    <td className="px-3 py-1.5"><ContainerLink hostId={hostConfig.hostId} containerId={e.id} name={e.name}/></td>
                                                    <td className="px-3 py-1.5"><Mono>{e.ipv4 ?? "—"}</Mono></td>
                                                    <td className="px-3 py-1.5"><Mono>{e.ipv6 ?? "—"}</Mono></td>
                                                    <td className="px-3 py-1.5 text-muted-foreground"><Mono>{e.mac ?? "—"}</Mono></td>
                                                    <td className="px-3 py-1.5 text-right">
                                                        {e.state && <Badge variant="outline" className={e.state === "running" ? "text-green-600" : ""}>{e.state}</Badge>}
                                                    </td>
                                                </tr>
                                            ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : <p className="text-sm text-muted-foreground">
                                    No containers are connected.{!builtin && " It will be removed by \"Prune networks\"."}
                                </p>}
                            </Section>
                            <Section title="Details">
                                <PropList rows={[
                                    ["Network ID", <Mono>{network.Id}</Mono>],
                                    ["Driver", network.Driver],
                                    ["Scope", network.Scope],
                                    ["Created", created?.toLocaleString()],
                                    ["IPv4", <Bool value={network.EnableIPv4 ?? true}/>],
                                    ["IPv6", <Bool value={network.EnableIPv6}/>],
                                    ["Internal", <Bool value={network.Internal}/>],
                                    ["Attachable", <Bool value={network.Attachable}/>],
                                    ["Ingress", <Bool value={network.Ingress}/>],
                                    ["Config only", <Bool value={network.ConfigOnly}/>],
                                    ["Config from", network.ConfigFrom?.Network],
                                    ["Compose project", project],
                                    ["Compose network", network.Labels?.["com.docker.compose.network"]],
                                ]}/>
                            </Section>
                        </TabsContent>

                        <TabsContent value="ipam" className="space-y-5">
                            <Section title="IPAM">
                                <PropList rows={[["Driver", network.IPAM?.Driver]]}/>
                            </Section>
                            <Section title={`Pools (${ipam.length})`}>
                                {ipam.length > 0 ? (
                                    <div className="space-y-2">
                                        {ipam.map((c, i) => (
                                            <div key={i} className="rounded-md border px-3">
                                                <PropList rows={[
                                                    ["Subnet", c.Subnet && <Mono>{c.Subnet}</Mono>],
                                                    ["Gateway", c.Gateway && <Mono>{c.Gateway}</Mono>],
                                                    ["IP range", c.IPRange && <Mono>{c.IPRange}</Mono>],
                                                    ...Object.entries(c.AuxiliaryAddresses ?? {}).map(([k, v]) =>
                                                        [`Aux: ${k}`, <Mono>{v as string}</Mono>] as [string, React.ReactNode]),
                                                ]}/>
                                            </div>
                                        ))}
                                    </div>
                                ) : <p className="text-sm text-muted-foreground">No address pools.</p>}
                            </Section>
                            {Object.keys(network.IPAM?.Options ?? {}).length > 0 && (
                                <Section title="IPAM options">
                                    <KeyValues entries={Object.entries(network.IPAM.Options) as [string, string][]}/>
                                </Section>
                            )}
                        </TabsContent>

                        <TabsContent value="labels"><KeyValues entries={labels}/></TabsContent>
                        <TabsContent value="options"><KeyValues entries={options}/></TabsContent>
                        <TabsContent value="raw"><RawJson data={network} name="network"/></TabsContent>
                    </div>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
};

export default DockerNetworkDetailsDialog;
