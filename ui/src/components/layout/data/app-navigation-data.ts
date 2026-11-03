import {AppNavigationData} from "@/components/layout/data/types.ts";
import {CloudIcon, SatelliteIcon} from "lucide-react";

export const appNavigationData: AppNavigationData = {
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
    // navInventory: [
    //     {
    //         title: "Kitchensink",
    //         url: "/kitchensink",
    //         //icon: IconTool,
    //         iconName: "kitchensink",
    //     },
    // ],
    // navFindings: [
    //     {
    //         title: "Findings",
    //         url: "/findings",
    //         //icon: IconTool,
    //         iconName: "findings",
    //     },
    //     {
    //         title: "Critical",
    //         iconName: "error",
    //         isActive: true,
    //         url: "#",
    //         items: [
    //             {
    //                 title: "Active Proposals",
    //                 url: "#",
    //             },
    //             {
    //                 title: "Archived",
    //                 url: "#",
    //             },
    //         ],
    //     },
    //     {
    //         title: "Warnings",
    //         iconName: "warning",
    //         url: "#",
    //         items: [
    //             {
    //                 title: "Active Proposals",
    //                 url: "#",
    //             },
    //             {
    //                 title: "Archived",
    //                 url: "#",
    //             },
    //         ],
    //     },
    //     {
    //         title: "Info",
    //         iconName: "info",
    //         url: "#",
    //         items: [
    //             {
    //                 title: "Active Proposals",
    //                 url: "#",
    //             },
    //             {
    //                 title: "Archived",
    //                 url: "#",
    //             },
    //         ],
    //     },
    // ]
};

export const appSidebarData: any = {
    environments: [
        {
            name: "Local",
            logo: SatelliteIcon,
            plan: "Basic",
        },
        {
            name: "Cloud",
            logo: CloudIcon,
            plan: "Pro",
        },
    ],
};