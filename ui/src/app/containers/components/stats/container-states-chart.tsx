import {Bar, BarChart, CartesianGrid, XAxis, YAxis} from "recharts";
import {
    ChartContainer,
    ChartLegend,
    ChartLegendContent,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {barHeight, StatsSection, stateConfig, tooltipRow} from "@/app/containers/components/stats/stats-ui.tsx";

const ContainerStatesChart = ({stats}: { stats: HostStats[] }) => {
    const data = stats.map((s) => ({host: s.hostId, ...s.containers}));
    return (
        <StatsSection title="Containers by host" description="Running, paused and stopped">
            <ChartContainer config={stateConfig} className="aspect-auto w-full" style={barHeight(data.length)}>
                <BarChart data={data} layout="vertical" margin={{left: 8, right: 8}}>
                    <CartesianGrid horizontal={false} />
                    <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                    <YAxis type="category" dataKey="host" width={110} tickLine={false} axisLine={false} />
                    <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(stateConfig, String)} />} />
                    <ChartLegend content={<ChartLegendContent />} />
                    <Bar dataKey="running" stackId="state" fill="var(--color-running)" />
                    <Bar dataKey="paused" stackId="state" fill="var(--color-paused)" />
                    <Bar dataKey="stopped" stackId="state" fill="var(--color-stopped)" radius={[0, 4, 4, 0]} />
                </BarChart>
            </ChartContainer>
        </StatsSection>
    );
};

export default ContainerStatesChart;
