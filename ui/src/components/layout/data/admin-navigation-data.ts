import {AdminNavigationData} from "@/components/layout/data/types.ts";

export const adminNavigationData: AdminNavigationData = {
    navAdmin: [
        {
            title: "Settings",
            url: "/admin/settings",
            iconName: "settings",
        },
        {
            title: "RPC",
            url: "/admin/rpc",
            //icon: IconDashboard,
            iconName: "xterm",
        },
        {
            title: "Tools",
            url: "/admin/tools",
            //icon: IconTool,
            iconName: "tool",
        },
    ],
};