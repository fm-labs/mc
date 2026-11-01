import {Bar, BarChart, CartesianGrid, XAxis, YAxis} from "recharts";
import {ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent} from "@/components/ui/chart.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {densityRows} from "@/app/containers/components/stats/insights.ts";
import {barHeight, EmptyNote, StatsSection, tooltipRow} from "@/app/containers/components/stats/stats-ui.tsx";

const cpuConfig = {perCpu: {label: "Running per CPU", color: "var(--chart-2)"}} satisfies ChartConfig;
const memConfig = {perGb: {label: "Running per GB RAM", color: "var(--chart-3)"}} satisfies ChartConfig;

const DensityBars = ({data, dataKey, config}: {
    data: ReturnType<typeof densityRows>
    dataKey: "perCpu" | "perGb"
    config: ChartConfig
}) => {
    const sorted = [...data].sort((a, b) => b[dataKey] - a[dataKey]);
    return (
        <ChartContainer config={config} className="aspect-auto w-full" style={barHeight(sorted.length)}>
            <BarChart data={sorted} layout="vertical" margin={{left: 8, right: 8}}>
                <CartesianGrid horizontal={false} />
                <XAxis type="number" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="host" width={110} tickLine={false} axisLine={false} />
                <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(config, (v) => v.toFixed(2))} />} />
                <Bar dataKey={dataKey} fill={`var(--color-${dataKey})`} radius={[0, 4, 4, 0]} />
            </BarChart>
        </ChartContainer>
    );
};

// Running containers relative to host capacity, to spot over- and underused hosts
const DensityChart = ({stats}: { stats: HostStats[] }) => {
    const data = densityRows(stats);
    return (
        <div className="grid gap-4 lg:grid-cols-2">
            <StatsSection title="Containers per CPU" description="Running containers per CPU core">
                {data.length ? <DensityBars data={data} dataKey="perCpu" config={cpuConfig} /> : <EmptyNote>No engine info cached</EmptyNote>}
            </StatsSection>
            <StatsSection title="Containers per GB RAM" description="Running containers per GB of host memory">
                {data.length ? <DensityBars data={data} dataKey="perGb" config={memConfig} /> : <EmptyNote>No engine info cached</EmptyNote>}
            </StatsSection>
        </div>
    );
};

export default DensityChart;
