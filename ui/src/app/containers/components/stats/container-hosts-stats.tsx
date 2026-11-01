import {useSearchParams} from "react-router";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx";
import {Button} from "@/components/ui/button.tsx";
import {useHostsStats} from "@/app/containers/components/stats/use-hosts-stats.ts";
import {attentionItems} from "@/app/containers/components/stats/insights.ts";
import OverviewTiles from "@/app/containers/components/stats/overview-tiles.tsx";
import {DiskByHostChart, DiskByTypeChart} from "@/app/containers/components/stats/disk-usage-charts.tsx";
import ContainerStatesChart from "@/app/containers/components/stats/container-states-chart.tsx";
import HostCard from "@/app/containers/components/stats/host-card.tsx";
import MissingHosts from "@/app/containers/components/stats/missing-hosts.tsx";
import AttentionPanel from "@/app/containers/components/stats/attention-panel.tsx";
import WarningsPanel from "@/app/containers/components/stats/warnings-panel.tsx";
import ResourcePolicyPanel from "@/app/containers/components/stats/resource-policy-panel.tsx";
import CleanupPotential from "@/app/containers/components/stats/cleanup-potential.tsx";
import {
    ImageAgeChart,
    ImageUsageChart,
    StaleImagesTable,
    UnusedImagesTable,
} from "@/app/containers/components/stats/image-usage.tsx";
import VolumeHealth from "@/app/containers/components/stats/volume-health.tsx";
import ComposeProjects from "@/app/containers/components/stats/compose-projects.tsx";
import PortMap from "@/app/containers/components/stats/port-map.tsx";
import VersionDrift from "@/app/containers/components/stats/version-drift.tsx";
import DensityChart from "@/app/containers/components/stats/density-chart.tsx";

const TABS = ["overview", "health", "storage", "workloads", "hosts"] as const;

// Container stats across all hosts, built only from data cached in this browser session
const ContainerHostsStats = () => {
    const {hosts, stats, missing, reload} = useHostsStats();
    const [params, setParams] = useSearchParams();
    const tab = TABS.includes(params.get("tab") as typeof TABS[number]) ? params.get("tab")! : "overview";

    if (hosts.length === 0) {
        return <div className="p-4 text-sm text-muted-foreground">No container hosts configured.</div>;
    }

    const attention = attentionItems(stats).length;

    return (
        <div className="space-y-4 p-4">
            <div className="flex items-center justify-between gap-2">
                <p className="text-sm text-muted-foreground">
                    Data cached in this browser session for {stats.length} of {hosts.length} hosts.
                    Open a host to load or refresh its data.
                </p>
                <Button variant="outline" size="sm" onClick={reload}>Reload</Button>
            </div>

            {stats.length > 0 && (
                <Tabs value={tab} onValueChange={(t) => setParams({tab: t}, {replace: true})} className="gap-4">
                    <TabsList>
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="health">Health{attention > 0 && ` (${attention})`}</TabsTrigger>
                        <TabsTrigger value="storage">Storage</TabsTrigger>
                        <TabsTrigger value="workloads">Workloads</TabsTrigger>
                        <TabsTrigger value="hosts">Hosts</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                        <OverviewTiles stats={stats} hostCount={hosts.length} />
                        <div className="grid gap-4 lg:grid-cols-3">
                            <DiskByHostChart stats={stats} className="lg:col-span-2" />
                            <DiskByTypeChart stats={stats} />
                        </div>
                        <ContainerStatesChart stats={stats} />
                        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                            {stats.map((s) => <HostCard key={s.hostId} stats={s} />)}
                        </div>
                    </TabsContent>

                    <TabsContent value="health" className="space-y-4">
                        <AttentionPanel stats={stats} />
                        <WarningsPanel stats={stats} />
                        <ResourcePolicyPanel stats={stats} />
                    </TabsContent>

                    <TabsContent value="storage" className="space-y-4">
                        <CleanupPotential stats={stats} />
                        <div className="grid gap-4 lg:grid-cols-2">
                            <ImageAgeChart stats={stats} />
                            <ImageUsageChart stats={stats} />
                        </div>
                        <div className="grid gap-4 lg:grid-cols-2">
                            <StaleImagesTable stats={stats} />
                            <UnusedImagesTable stats={stats} />
                        </div>
                        <VolumeHealth stats={stats} />
                    </TabsContent>

                    <TabsContent value="workloads" className="space-y-4">
                        <ComposeProjects stats={stats} />
                        <PortMap stats={stats} />
                    </TabsContent>

                    <TabsContent value="hosts" className="space-y-4">
                        <VersionDrift stats={stats} />
                        <DensityChart stats={stats} />
                    </TabsContent>
                </Tabs>
            )}

            <MissingHosts hostIds={missing} />
        </div>
    );
};

export default ContainerHostsStats;
