// The local mc. Requests for it go out without an x-mc-node header.
export const LOCAL_NODE = "localhost";

/**
 * Headers that send a request to a node through the node proxy (MC_NODE_PROXY_ENABLED).
 * No header for the local mc.
 */
export const nodeHeaders = (node?: string | null): Record<string, string> =>
    node && node !== LOCAL_NODE ? { "x-mc-node": node } : {};
