const ITEM_TYPE_MAP: Record<string, { actions?: string[], views?: string[], widgets?: string[] }> = {
    clouds: {
        views: ["details", "settings"],
    },
    container_image: {
        views: ["findings"],
        widgets: ["xscan"]
    },
    repository: {
        views: ["findings"],
        widgets: ["github-repository"],
    },
    "dns-domain": {
        views: ["details", "webcheck"],
        widgets: [],
    },
};

export const getItemTypeActions = (itemType: string) => {
    return ITEM_TYPE_MAP[itemType]?.actions || [];
};

export const getItemTypeViews = (itemType: string) => {
    return ITEM_TYPE_MAP[itemType]?.views || [];
};

export const getItemTypeWidgets = (itemType: string) => {
    return ITEM_TYPE_MAP[itemType]?.widgets || [];
};
