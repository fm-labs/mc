// Client-side mirror of the AppVolumeSpec / AppNetworkSpec validators in apps_helper.py
import { AppNetworkSpec, AppVolumeSpec } from "@/features/apps/apps.types.ts";

const RESOURCE_NAME_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/;

const duplicates = (names: string[]) =>
    new Set(names.filter((n, i) => n && names.indexOf(n) !== i));

/** One error message (or null) per volume row. */
export const validateVolumes = (volumes: AppVolumeSpec[]): (string | null)[] => {
    const dupes = duplicates(volumes.map((v) => v.volume_name.trim()));
    return volumes.map((v) => {
        const name = v.volume_name.trim();
        if (!RESOURCE_NAME_PATTERN.test(name)) return "Volume name: letters, digits, '_', '.' and '-'.";
        if (dupes.has(name)) return `Duplicate volume '${name}'.`;
        if (!v.container_path.trim().startsWith("/")) return "Container path must be absolute (start with '/').";
        if (v.bind && !(v.host_path || "").trim()) return "Host path is required for bind mounts.";
        return null;
    });
};

/** One error message (or null) per network row. */
export const validateNetworks = (networks: AppNetworkSpec[]): (string | null)[] => {
    const dupes = duplicates(networks.map((n) => n.network_name.trim()));
    return networks.map((n) => {
        const name = n.network_name.trim();
        if (!RESOURCE_NAME_PATTERN.test(name)) return "Network name: letters, digits, '_', '.' and '-'.";
        if (dupes.has(name)) return `Duplicate network '${name}'.`;
        return null;
    });
};

/** Payload shape the API expects: trimmed, host_path only for bind mounts. */
export const normalizeVolumes = (volumes: AppVolumeSpec[]): AppVolumeSpec[] =>
    volumes.map((v) => ({
        volume_name: v.volume_name.trim(),
        container_path: v.container_path.trim(),
        bind: !!v.bind,
        host_path: v.bind ? (v.host_path || "").trim() : null,
    }));

export const normalizeNetworks = (networks: AppNetworkSpec[]): AppNetworkSpec[] =>
    networks.map((n) => ({ network_name: n.network_name.trim(), external: !!n.external }));
