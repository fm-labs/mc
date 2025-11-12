import {
    IconCamera,
    IconFileAi,
    IconFileDescription,
} from "@tabler/icons-react";
import { AppNavigationData } from "@/components/layout/data/types.ts";

export const navigationData: AppNavigationData = {
    // user: {
    //     name: "shadcn",
    //     email: "m@example.com",
    //     avatar: "/avatars/shadcn.jpg",
    // },
    navMain: [
        {
            title: "Dashboard",
            url: "/dashboard",
            //icon: IconDashboard,
            iconName: "dashboard",
        },
        {
            title: "My Servers",
            url: "/infrastructure",
            //icon: IconTool,
            iconName: "network",
        },
        {
            title: "My Clouds",
            url: "/infrastructure/aws",
            //icon: IconTool,
            iconName: "aws",
        },
        {
            title: "My Repositories",
            url: "/repositories",
            //icon: IconTool,
            iconName: "repository",
        },
        {
            title: "My Applications",
            url: "/stacks",
            //icon: IconTool,
            iconName: "stacks",
        },
        // {
        //     title: "Domains",
        //     url: "/infrastructure/domains",
        //     //icon: IconTool,
        //     iconName: "domain",
        // },
        // {
        //     title: "Containers",
        //     url: "/containers",
        //     //icon: IconTool,
        //     iconName: "container",
        // },
    ],
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
        {
            title: "Settings",
            url: "/settings/profile",
            iconName: "settings",
        },
        {
            title: "Tools",
            url: "/admin/tools",
            //icon: IconTool,
            iconName: "tool",
        },
        {
            title: "Integrations",
            url: "/admin/integrations",
            //icon: IconTool,
            iconName: "apps",
        },
        {
            title: "Tasks",
            url: "/admin/tasks",
            //icon: IconTool,
            iconName: "tasks",
        },
        {
            title: "Ansible",
            url: "/admin/ansible",
            //icon: IconTool,
            iconName: "ansible",
        },
        {
            title: "MCP Servers",
            url: "/mcp-servers",
            //icon: IconTool,
            iconName: "mcp",
        },
        // {
        //     title: "Docker MCP",
        //     url: "/docker-mcp",
        //     //icon: IconTool,
        //     iconName: "docker-mcp",
        // },
        // {
        //     title: "Xterm",
        //     url: "/xterm",
        //     //icon: IconTool,
        //     iconName: "xterm",
        // },
        // {
        //     title: "Get Help",
        //     url: "/",
        //     icon: IconHelp,
        // },
        // {
        //     title: "Search",
        //     url: "#",
        //     icon: IconSearch,
        // },
        // {
        //     title: "Access Control",
        //     url: "#",
        //     icon: IconUsers,
        // },
    ],
    // navInventory: [
    //     // {
    //     //     title: "Repositories",
    //     //     url: "/inventory/repository",
    //     //     //icon: IconListDetails,
    //     //     iconName: "repository",
    //     // },
    //     // {
    //     //     title: "Hosts",
    //     //     url: "/inventory/host",
    //     //     //icon: IconCloud,
    //     //     iconName: "server",
    //     // },
    //     // {
    //     //     title: "Clouds",
    //     //     url: "/inventory/cloud",
    //     //     //icon: IconCloud,
    //     //     iconName: "cloud",
    //     // },
    //     // {
    //     //     title: "Container Images",
    //     //     url: "/inventory/container-image",
    //     //     //icon: IconContainer,
    //     //     iconName: "container",
    //     // },
    //     // {
    //     //     title: "Domains",
    //     //     url: "/inventory/dns-domain",
    //     //     //icon: IconGlobe,
    //     //     iconName: "globe",
    //     // },
    //     // {
    //     //     title: "Container Hosts",
    //     //     url: "/inventory/container-host",
    //     //     //icon: IconGlobe,
    //     //     iconName: "container",
    //     // },
    //     // {
    //     //     title: "Compose Apps",
    //     //     url: "/inventory/compose-app",
    //     //     //icon: IconGlobe,
    //     //     iconName: "apps",
    //     // },
    //     // {
    //     //     name: "Data Library",
    //     //     url: "#",
    //     //     icon: IconDatabase,
    //     // },
    //     // {
    //     //     name: "Reports",
    //     //     url: "#",
    //     //     icon: IconReport,
    //     // },
    //     // {
    //     //     name: "Word Assistant",
    //     //     url: "#",
    //     //     icon: IconFileWord,
    //     // },
    // ],
};
