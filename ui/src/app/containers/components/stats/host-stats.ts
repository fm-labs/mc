import {readCached} from "@/utils/session-cache.ts";
import {
    ContainerAttrs,
    DfImage,
    DockerDf,
    DockerInfo,
    ImageAttrs,
} from "@/app/containers/components/stats/docker-types.ts";

export type DiskUsage = {
    images: number
    containers: number
    volumes: number
    buildCache: number
}

export type CountSize = { count: number, size: number }

export type HostStats = {
    hostId: string
    info?: DockerInfo
    df?: DockerDf
    // full container / image lists, only present when the host page has loaded them
    containerList?: ContainerAttrs[]
    imageList?: ImageAttrs[]
    cachedAt: { info?: number, df?: number, containers?: number, images?: number }
    containers: { total: number, running: number, paused: number, stopped: number }
    imageCount: number
    volumeCount: number
    disk?: DiskUsage
    reclaimable?: DiskUsage
    cleanup?: {
        danglingImages: CountSize
        unusedImages: CountSize
        stoppedContainers: CountSize
        orphanVolumes: CountSize
        buildCache: CountSize
    }
    topImages: { name: string, size: number }[]
}

export const EMPTY_DISK: DiskUsage = {images: 0, containers: 0, volumes: 0, buildCache: 0};

// Docker reports -1 when a size was not computed
export const size = (n?: number | null) => (typeof n === "number" && n > 0 ? n : 0);

const sum = <T, >(items: T[] | null | undefined, fn: (item: T) => number) =>
    (items ?? []).reduce((acc, item) => acc + fn(item), 0);

const countSize = <T, >(items: T[] | null | undefined, fn: (item: T) => number): CountSize =>
    ({count: items?.length ?? 0, size: sum(items, fn)});

export const shortId = (id: string) => id.replace("sha256:", "").slice(0, 12);

export const isDangling = (img: { RepoTags?: string[] | null }) =>
    !img.RepoTags?.some((t) => t !== "<none>:<none>");

export const imageName = (img: { Id: string, RepoTags?: string[] | null }) =>
    img.RepoTags?.find((t) => t !== "<none>:<none>") ?? shortId(img.Id);

export const containerName = (c: ContainerAttrs) => (c.Name ?? "").replace(/^\//, "") || shortId(c.Id);

// what an image would free when removed (layers shared with other images stay)
const uniqueSize = (i: DfImage) => size(i.Size) - size(i.SharedSize);

export const diskTotal = (d?: DiskUsage) => d ? d.images + d.containers + d.volumes + d.buildCache : 0;

export const sumDisk = (list: (DiskUsage | undefined)[]): DiskUsage =>
    list.reduce<DiskUsage>((acc, d) => d ? {
        images: acc.images + d.images,
        containers: acc.containers + d.containers,
        volumes: acc.volumes + d.volumes,
        buildCache: acc.buildCache + d.buildCache,
    } : acc, EMPTY_DISK);

export const diskUsage = (df: DockerDf): DiskUsage => ({
    // same as `docker system df`: layers are counted once
    images: size(df.LayersSize) || sum(df.Images, uniqueSize),
    containers: sum(df.Containers, (c) => size(c.SizeRw)),
    volumes: sum(df.Volumes, (v) => size(v.UsageData?.Size)),
    buildCache: sum(df.BuildCache?.filter((b) => !b.Shared), (b) => size(b.Size)),
});

export const cleanupStats = (df: DockerDf): NonNullable<HostStats["cleanup"]> => {
    const unused = df.Images?.filter((i) => !i.Containers);
    return {
        danglingImages: countSize(unused?.filter(isDangling), uniqueSize),
        unusedImages: countSize(unused, uniqueSize),
        stoppedContainers: countSize(df.Containers?.filter((c) => c.State !== "running" && c.State !== "paused"), (c) => size(c.SizeRw)),
        orphanVolumes: countSize(df.Volumes?.filter((v) => !v.UsageData?.RefCount), (v) => size(v.UsageData?.Size)),
        buildCache: countSize(df.BuildCache?.filter((b) => !b.InUse && !b.Shared), (b) => size(b.Size)),
    };
};

const containerCounts = (info?: DockerInfo, df?: DockerDf, list?: ContainerAttrs[]) => {
    if (info && typeof info.Containers === "number") {
        return {
            total: info.Containers,
            running: info.ContainersRunning ?? 0,
            paused: info.ContainersPaused ?? 0,
            stopped: info.ContainersStopped ?? 0,
        };
    }
    const states = list?.map((c) => c.State?.Status) ?? df?.Containers?.map((c) => c.State) ?? [];
    const running = states.filter((s) => s === "running").length;
    const paused = states.filter((s) => s === "paused").length;
    return {total: states.length, running, paused, stopped: states.length - running - paused};
};

// Build stats for a host from the browser session cache only (never calls the API).
// Keys match the ones written by ContainerHostProvider.fetchContainerData.
export const readHostStats = (hostId: string): HostStats | null => {
    const key = (path: string) => `container_host_${hostId}_path_${path}`;
    const info = readCached<DockerInfo>(key("info"));
    const df = readCached<DockerDf>(key("df"));
    const containers = readCached<ContainerAttrs[]>(key("containers"));
    const images = readCached<ImageAttrs[]>(key("images"));
    if (!info?.data && !df?.data && !containers?.data) {
        return null;
    }
    const dfData = df?.data ?? undefined;
    const containerList = Array.isArray(containers?.data) ? containers.data : undefined;
    const imageList = Array.isArray(images?.data) ? images.data : undefined;
    const reclaim = dfData ? cleanupStats(dfData) : undefined;
    return {
        hostId,
        info: info?.data ?? undefined,
        df: dfData,
        containerList,
        imageList,
        cachedAt: {
            info: info?.timestamp,
            df: df?.timestamp,
            containers: containers?.timestamp,
            images: images?.timestamp,
        },
        containers: containerCounts(info?.data, dfData, containerList),
        imageCount: dfData?.Images?.length ?? imageList?.length ?? info?.data?.Images ?? 0,
        volumeCount: dfData?.Volumes?.length ?? 0,
        disk: dfData ? diskUsage(dfData) : undefined,
        cleanup: reclaim,
        reclaimable: reclaim ? {
            images: reclaim.unusedImages.size,
            containers: reclaim.stoppedContainers.size,
            volumes: reclaim.orphanVolumes.size,
            buildCache: reclaim.buildCache.size,
        } : undefined,
        topImages: (dfData?.Images ?? imageList ?? [])
            .map((i) => ({name: imageName(i), size: size(i.Size)}))
            .sort((a, b) => b.size - a.size)
            .slice(0, 5),
    };
};
