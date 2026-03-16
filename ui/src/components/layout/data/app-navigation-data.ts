import { AppNavigationData } from "@/components/layout/data/types.ts";

export const navigationData: AppNavigationData = {
    navMain: [
        {
            title: "Dashboard",
            url: "/dashboard",
            //icon: IconDashboard,
            iconName: "dashboard",
        },
        // {
        //     title: "My Servers",
        //     url: "/infrastructure",
        //     //icon: IconTool,
        //     iconName: "network",
        // },
        // {
        //     title: "My Clouds",
        //     url: "/infrastructure/aws",
        //     //icon: IconTool,
        //     iconName: "aws",
        // },
        // {
        //     title: "My Repositories",
        //     url: "/repositories",
        //     //icon: IconTool,
        //     iconName: "repository",
        // },
        {
            title: "My Applications",
            url: "/stacks",
            //icon: IconTool,
            iconName: "stacks",
        },
    ],
    navSecondary: [],
    navInventory: [
        {
            title: "Kitchensink",
            url: "/kitchensink",
            //icon: IconTool,
            iconName: "kitchensink",
        },
    ],
    navContainers: [
    ],
    navFindings: [
        {
            title: "Findings",
            url: "/findings",
            //icon: IconTool,
            iconName: "findings",
        },
        {
            title: "Critical",
            iconName: "error",
            isActive: true,
            url: "#",
            items: [
                {
                    title: "Active Proposals",
                    url: "#",
                },
                {
                    title: "Archived",
                    url: "#",
                },
            ],
        },
        {
            title: "Warnings",
            iconName: "warning",
            url: "#",
            items: [
                {
                    title: "Active Proposals",
                    url: "#",
                },
                {
                    title: "Archived",
                    url: "#",
                },
            ],
        },
        {
            title: "Info",
            iconName: "info",
            url: "#",
            items: [
                {
                    title: "Active Proposals",
                    url: "#",
                },
                {
                    title: "Archived",
                    url: "#",
                },
            ],
        },
    ],
    navAdmin: [
        // {
        //     title: "Settings",
        //     url: "/settings",
        //     iconName: "settings",
        // },
        {
            title: "RPC",
            url: "/admin/rpc",
            //icon: IconDashboard,
            iconName: "xterm",
        },
        // {
        //     title: "Tools",
        //     url: "/admin/tools",
        //     //icon: IconTool,
        //     iconName: "tool",
        // },
    ],
};
