// Mirrors the backend app specs in src/mc/plugin/apps/apps_helper.py

export type AppVolumeSpec = {
    volume_name: string;
    container_path: string;
    bind?: boolean;
    host_path?: string | null;
};

export type AppNetworkSpec = {
    network_name: string;
    external?: boolean;
};

export type AppSpec = {
    id: string;
    type: "container" | "compose";
    title?: string | null;
    description?: string | null;
    image?: string | null;
    stackfile?: string | null;
    volumes?: AppVolumeSpec[] | null;
    networks?: AppNetworkSpec[] | null;
    environment?: Record<string, string> | null;
};

export type AppSpecDetails = {
    spec: AppSpec;
    spec_path: string;
    stackfile_path?: string | null;
    stackfile_content?: string | null;
    // names declared at the top level of compose.yaml
    compose_volumes?: string[];
    compose_networks?: string[];
    // compose.override.yaml generated from the spec on save
    override_path?: string | null;
    override_content?: string | null;
    // only set by create / update: overrides that couldn't be applied
    compile_warnings?: string[];
};

export type CreateAppFromScratchRequest = {
    id: string;
    title?: string | null;
    description?: string | null;
    stackfile_content: string;
    volumes?: AppVolumeSpec[];
    networks?: AppNetworkSpec[];
};

export type UpdateAppSpecRequest = {
    title?: string | null;
    description?: string | null;
    stackfile_content?: string | null;
    volumes?: AppVolumeSpec[];
    networks?: AppNetworkSpec[];
};

// POST /apps/{id}/action/{action}
export type AppAction = "up" | "down" | "stop" | "restart";

// GET /apps/{id}/compiled
export type CompiledFile = {
    name: string;
    path: string;
    content: string;
};

export type CompiledAppSpec = {
    // compose files passed to docker compose, in order
    files: CompiledFile[];
    // `docker compose config` output: the files merged, with variables resolved
    merged?: string | null;
    merged_error?: string | null;
};
