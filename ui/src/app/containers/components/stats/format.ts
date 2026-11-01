export const formatBytes = (bytes: number, decimals = 1) => {
    if (!bytes || bytes < 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : decimals)} ${units[i]}`;
};

export const formatDuration = (ms: number) => {
    const s = Math.max(0, Math.round(ms / 1000));
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.round(s / 60)}m`;
    if (s < 86400) return `${Math.round(s / 3600)}h`;
    return `${Math.round(s / 86400)}d`;
};

export const formatAge = (timestamp?: number) =>
    timestamp ? `${formatDuration(Date.now() - timestamp)} ago` : "—";

export const DAY = 86400 * 1000;
