import {Bar, BarChart, CartesianGrid, Cell, Label, Pie, PieChart, XAxis, YAxis} from "recharts";
import {
    ChartContainer,
    ChartLegend,
    ChartLegendContent,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart.tsx";
import {diskTotal, HostStats, sumDisk} from "@/app/containers/components/stats/host-stats.ts";
import {formatBytes} from "@/app/containers/components/stats/format.ts";
import {
    barHeight,
    diskConfig,
    diskKeys,
    EmptyNote,
    StatsSection,
    tooltipRow,
} from "@/app/containers/components/stats/stats-ui.tsx";

export const DiskByHostChart = ({stats, className}: { stats: HostStats[], className?: string }) => {
    const data = stats.filter((s) => s.disk).map((s) => ({host: s.hostId, ...s.disk}));
    return (
        <StatsSection title="Disk usage by host" description="From docker system df" className={className}>
            {data.length > 0 ? (
                <ChartContainer config={diskConfig} className="aspect-auto w-full" style={barHeight(data.length)}>
                    <BarChart data={data} layout="vertical" margin={{left: 8, right: 8}}>
                        <CartesianGrid horizontal={false} />
                        <XAxis type="number" tickFormatter={(v) => formatBytes(v, 0)} tickLine={false} axisLine={false} />
                        <YAxis type="category" dataKey="host" width={110} tickLine={false} axisLine={false} />
                        <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(diskConfig, formatBytes)} />} />
                        <ChartLegend content={<ChartLegendContent />} />
                        {diskKeys.map((k, i) => (
                            <Bar key={k} dataKey={k} stackId="disk" fill={`var(--color-${k})`}
                                 radius={i === diskKeys.length - 1 ? [0, 4, 4, 0] : 0} />
                        ))}
                    </BarChart>
                </ChartContainer>
            ) : <EmptyNote>No disk usage cached</EmptyNote>}
        </StatsSection>
    );
};

export const DiskByTypeChart = ({stats, className}: { stats: HostStats[], className?: string }) => {
    const disk = sumDisk(stats.map((s) => s.disk));
    const total = diskTotal(disk);
    const data = diskKeys
        .map((k) => ({type: k, value: disk[k], fill: diskConfig[k].color}))
        .filter((d) => d.value > 0);

    return (
        <StatsSection title="Disk usage by type" description="All hosts" className={className}>
            {data.length > 0 ? (
                <ChartContainer config={diskConfig} className="mx-auto aspect-square max-h-[260px]">
                    <PieChart>
                        <ChartTooltip content={<ChartTooltipContent hideLabel nameKey="type" formatter={tooltipRow(diskConfig, formatBytes)} />} />
                        <Pie data={data} dataKey="value" nameKey="type" innerRadius={60} strokeWidth={4}>
                            {data.map((d) => <Cell key={d.type} fill={d.fill} />)}
                            <Label content={({viewBox}) => {
                                if (!viewBox || !("cx" in viewBox)) return null;
                                return (
                                    <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle">
                                        <tspan x={viewBox.cx} y={viewBox.cy} className="fill-foreground text-xl font-bold">
                                            {formatBytes(total)}
                                        </tspan>
                                        <tspan x={viewBox.cx} y={(viewBox.cy ?? 0) + 20} className="fill-muted-foreground">
                                            total
                                        </tspan>
                                    </text>
                                );
                            }} />
                        </Pie>
                        <ChartLegend content={<ChartLegendContent nameKey="type" />} />
                    </PieChart>
                </ChartContainer>
            ) : <EmptyNote>No disk usage cached</EmptyNote>}
        </StatsSection>
    );
};
