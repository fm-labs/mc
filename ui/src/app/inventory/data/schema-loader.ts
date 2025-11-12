

type JSONSchema = unknown;

export const schemaLoaders = {
    "dns-domain": () => import("@/app/inventory/data/schemas/dns-domain-schema"),
    "repository": () => import("@/app/inventory/data/schemas/repository-schema"),
} satisfies Record<string, () => Promise<{ default: JSONSchema }>>

export async function loadSchema(itemType: string): Promise<JSONSchema | null> {
    // @ts-ignore
    const loader = schemaLoaders[itemType];
    if (!loader) return null;
    const mod = await loader();
    return mod.default;
}
