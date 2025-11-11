"use client"

import * as React from "react"

import {
    SidebarGroup,
    SidebarGroupContent,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar.tsx"
import AppIcon from "@/components/app-icon.tsx";
import {NavigationItem} from "@/components/layout/data/types.ts";
import {Link} from "react-router";
import {Badge} from "@/components/ui/badge.tsx";

export function NavFindings({
                                 items,
                                 ...props
                             }: {
    items: NavigationItem[]
} & React.ComponentPropsWithoutRef<typeof SidebarGroup>) {
    return (
        <SidebarGroup {...props}>
            <SidebarGroupContent>
                <SidebarMenu>
                    {items && items.map((item) => (
                        <SidebarMenuItem key={item.title}>
                            <SidebarMenuButton asChild>
                                <div className={"flex flex-row justify-between w-full"}>
                                    <div className={"flex flex-row gap-2 items-center"}>
                                        <span>
                                            <AppIcon icon={item?.iconName}/>
                                        </span>
                                        <span>
                                            <Link to={item.url}>{item.title}</Link>
                                        </span>
                                    </div>
                                    <div>
                                        <Badge className={""}>0</Badge>
                                    </div>
                                </div>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    ))}
                </SidebarMenu>
            </SidebarGroupContent>
        </SidebarGroup>
    )
}
