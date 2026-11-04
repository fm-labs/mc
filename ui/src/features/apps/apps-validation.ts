// Client-side mirror of the AppVolumeSpec / AppNetworkSpec validators in apps_helper.py
import { AppNetworkSpec, AppRoutingMode, AppRoutingSpec, AppVolumeSpec } from "@/features/apps/apps.types.ts";

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

// Environment variables, mirrors ENV_NAME_PATTERN / RESERVED_ENV_NAMES in apps_helper.py
const ENV_NAME_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;
const RESERVED_ENV_NAMES = new Set(["DOCKER_HOST", "COMPOSE_PROJECT_DIRECTORY", "COMPOSE_PROJECT_NAME"]);

/** One editor row. A list (not a map) so rows keep their order and can be blank while typing. */
export type EnvVarRow = { name: string; value: string };

const isBlankRow = (r: EnvVarRow) => !r.name.trim() && !r.value;

export const envToRows = (env: Record<string, string> | null | undefined): EnvVarRow[] =>
    Object.entries(env ?? {}).map(([name, value]) => ({ name, value }));

/** Blank rows are dropped. Values are kept as typed (whitespace can matter). */
export const rowsToEnv = (rows: EnvVarRow[]): Record<string, string> =>
    Object.fromEntries(rows.filter((r) => !isBlankRow(r)).map((r) => [r.name.trim(), r.value]));

/** One error message (or null) per row. */
export const validateEnvironment = (rows: EnvVarRow[]): (string | null)[] => {
    const dupes = duplicates(rows.map((r) => r.name.trim()));
    return rows.map((r) => {
        if (isBlankRow(r)) return null;
        const name = r.name.trim();
        if (!name) return "Variable name is required.";
        if (!ENV_NAME_PATTERN.test(name)) return "Name: letters, digits and '_', not starting with a digit.";
        if (RESERVED_ENV_NAMES.has(name)) return `${name} is set by mc and can't be overridden.`;
        if (dupes.has(name)) return `Duplicate variable '${name}'.`;
        return null;
    });
};

/** Variable names referenced in a compose file as ${NAME} or $NAME (not $$ escapes). */
export const composeVariableRefs = (compose: string): string[] => {
    const names = new Set<string>();
    for (const m of compose.matchAll(/(\$+)\{?([A-Za-z_][A-Za-z0-9_]*)/g)) {
        if (m[1].length % 2 === 1) names.add(m[2]);
    }
    return [...names].sort();
};

// Routes, mirrors AppRoutingSpec in apps_helper.py
const SERVICE_NAME_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/;
const DOMAIN_NAME_PATTERN = /^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$/;

/** One editor row. Port and domains stay text while typing. */
export type RouteRow = { service_name: string; container_port: string; mode: AppRoutingMode; domains: string };

/** Domains are separated by commas, spaces or new lines. */
export const parseDomains = (domains: string): string[] => [
    ...new Set(domains.split(/[\s,]+/).map((d) => d.trim().toLowerCase().replace(/\.$/, "")).filter(Boolean)),
];

export const routingToRows = (routing: AppRoutingSpec[] | null | undefined): RouteRow[] =>
    (routing ?? []).map((r) => ({
        service_name: r.service_name,
        container_port: String(r.container_port),
        mode: r.mode,
        domains: r.domain_names.join(", "),
    }));

export const rowsToRouting = (rows: RouteRow[]): AppRoutingSpec[] =>
    rows.map((r) => ({
        service_name: r.service_name.trim(),
        container_port: Number(r.container_port),
        mode: r.mode,
        domain_names: parseDomains(r.domains),
    }));

/** One error message (or null) per route row. */
export const validateRouting = (rows: RouteRow[]): (string | null)[] => {
    const targets = rows.map((r) => `${r.service_name.trim()}:${r.container_port.trim()}`);
    const dupes = duplicates(targets);
    return rows.map((r, i) => {
        if (!SERVICE_NAME_PATTERN.test(r.service_name.trim())) return "Service: letters, digits, '_', '.' and '-'.";
        const port = Number(r.container_port);
        if (!/^\d+$/.test(r.container_port.trim()) || port < 1 || port > 65535) return "Port must be 1-65535.";
        const domains = parseDomains(r.domains);
        if (domains.length === 0) return "At least one domain name is required.";
        const bad = domains.find((d) => !DOMAIN_NAME_PATTERN.test(d));
        if (bad) return `Invalid domain name '${bad}'.`;
        if (dupes.has(targets[i])) return `Duplicate route to ${targets[i]}. Put all its domains in one route.`;
        return null;
    });
};
