import {AdminNavigationData} from "@/components/layout/data/types.ts";

export const adminNavigationData: AdminNavigationData = {
    navAdmin: [
        {
            title: "Apps",
            url: "/admin/apps",
            iconName: "apps",
        },
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