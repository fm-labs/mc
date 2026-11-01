import {Bar, BarChart, CartesianGrid, XAxis, YAxis} from "recharts";
import {
    ChartConfig,
    ChartContainer,
    ChartLegend,
    ChartLegendContent,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart.tsx";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import {HostStats} from "@/app/containers/components/stats/host-stats.ts";
import {DAY, formatBytes} from "@/app/containers/components/stats/format.ts";
import {
    hostsWithContainerList,
    imageAgeBuckets,
    imageRows,
    STALE_IMAGE_DAYS,
    staleImages,
} from "@/app/containers/components/stats/insights.ts";
import {
    CoverageNote,
    EmptyNote,
    HostLink,
    StatsSection,
    tooltipRow,
    useRowLimit,
} from "@/app/containers/components/stats/stats-ui.tsx";

const ageConfig = {
    inUse: {label: "In use", color: "var(--chart-2)"},
    unused: {label: "Unused", color: "var(--chart-1)"},
} satisfies ChartConfig;

const usageConfig = {
    running: {label: "Running", color: "var(--chart-2)"},
    stopped: {label: "Stopped", color: "var(--chart-1)"},
} satisfies ChartConfig;

export const ImageAgeChart = ({stats}: { stats: HostStats[] }) => {
    const data = imageAgeBuckets(imageRows(stats));
    const hasData = data.some((d) => d.inUse + d.unused > 0);
    return (
        <StatsSection title="Image age" description="Images by build date, in use or not">
            {hasData ? (
                <ChartContainer config={ageConfig} className="aspect-auto h-[240px] w-full">
                    <BarChart data={data} margin={{left: -16, right: 8}}>
                        <CartesianGrid vertical={false} />
                        <XAxis dataKey="bucket" tickLine={false} axisLine={false} />
                        <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                        <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(ageConfig, String)} />} />
                        <ChartLegend content={<ChartLegendContent />} />
                        <Bar dataKey="inUse" stackId="age" fill="var(--color-inUse)" />
                        <Bar dataKey="unused" stackId="age" fill="var(--color-unused)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ChartContainer>
            ) : <EmptyNote>No image dates cached</EmptyNote>}
        </StatsSection>
    );
};

// which images run the most containers
export const ImageUsageChart = ({stats}: { stats: HostStats[] }) => {
    const byName = new Map<string, { running: number, total: number }>();
    imageRows(stats).forEach((r) => {
        if (!r.containers) return;
        const v = byName.get(r.name) ?? {running: 0, total: 0};
        byName.set(r.name, {running: v.running + r.running, total: v.total + r.containers});
    });
    const data = [...byName.entries()]
        .map(([image, v]) => ({image, running: v.running, stopped: Math.max(0, v.total - v.running)}))
        .sort((a, b) => (b.running + b.stopped) - (a.running + a.stopped))
        .slice(0, 10);

    return (
        <StatsSection title="Containers per image" description="Top 10 images, all hosts">
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {data.length > 0 ? (
                <ChartContainer config={usageConfig} className="aspect-auto w-full" style={{height: data.length * 32 + 60}}>
                    <BarChart data={data} layout="vertical" margin={{left: 8, right: 8}}>
                        <CartesianGrid horizontal={false} />
                        <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                        <YAxis type="category" dataKey="image" width={180} tickLine={false} axisLine={false}
                               tickFormatter={(v: string) => v.length > 28 ? `…${v.slice(-27)}` : v} />
                        <ChartTooltip content={<ChartTooltipContent formatter={tooltipRow(usageConfig, String)} />} />
                        <ChartLegend content={<ChartLegendContent />} />
                        <Bar dataKey="running" stackId="use" fill="var(--color-running)" />
                        <Bar dataKey="stopped" stackId="use" fill="var(--color-stopped)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ChartContainer>
            ) : <EmptyNote>No containers cached</EmptyNote>}
        </StatsSection>
    );
};

export const StaleImagesTable = ({stats}: { stats: HostStats[] }) => {
    const rows = staleImages(imageRows(stats));
    const {visible, toggle} = useRowLimit(rows, 10);
    const now = Date.now();
    return (
        <StatsSection title="Stale deployments"
                      description={`Running containers on images built more than ${STALE_IMAGE_DAYS} days ago`}>
            <CoverageNote have={hostsWithContainerList(stats)} total={stats.length} what="containers" />
            {rows.length === 0 ? <EmptyNote>No stale images in use.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Image</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead className="text-right">Age</TableHead>
                                <TableHead className="text-right">Running</TableHead>
                                <TableHead className="text-right">Size</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r) => (
                                <TableRow key={`${r.hostId}-${r.id}`}>
                                    <TableCell className="max-w-[280px] truncate font-mono text-xs" title={r.name}>{r.name}</TableCell>
                                    <TableCell><HostLink hostId={r.hostId} path="/images" /></TableCell>
                                    <TableCell className="text-right tabular-nums">{Math.round((now - r.created!) / DAY)}d</TableCell>
                                    <TableCell className="text-right tabular-nums">{r.running}</TableCell>
                                    <TableCell className="text-right tabular-nums text-muted-foreground">{formatBytes(r.size)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {toggle}
                </>
            )}
        </StatsSection>
    );
};

export const UnusedImagesTable = ({stats}: { stats: HostStats[] }) => {
    const rows = imageRows(stats)
        .filter((r) => r.containers === 0)
        .sort((a, b) => b.size - a.size);
    const {visible, toggle} = useRowLimit(rows, 10);
    const dangling = rows.filter((r) => r.dangling);
    return (
        <StatsSection title="Unused images"
                      description={`${rows.length} images without containers (${dangling.length} dangling, ${formatBytes(dangling.reduce((a, r) => a + r.size, 0))})`}>
            {rows.length === 0 ? <EmptyNote>No unused images.</EmptyNote> : (
                <>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Image</TableHead>
                                <TableHead>Host</TableHead>
                                <TableHead className="text-right">Size</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {visible.map((r) => (
                                <TableRow key={`${r.hostId}-${r.id}`}>
                                    <TableCell className="max-w-[280px] truncate font-mono text-xs" title={r.name}>
                                        {r.name}{r.dangling && <span className="ml-2 text-muted-foreground">(dangling)</span>}
                                    </TableCell>
                                    <TableCell><HostLink hostId={r.hostId} path="/images" /></TableCell>
                                    <TableCell className="text-right tabular-nums">{formatBytes(r.size)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {toggle}
                </>
            )}
        </StatsSection>
    );
};
