import * as React from "react";

import { NavMain } from "@/components/layout/nav-main.tsx";
import { NavUser } from "@/components/layout/nav-user.tsx";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
} from "@/components/ui/sidebar.tsx";
import { navigationData } from "@/components/layout/data/app-navigation-data.ts";
import { TeamSwitcher } from "@/components/layout/team-switcher.tsx";
import { appSidebarData } from "@/components/layout/data/app-sidebar-data.ts";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {

    return (
        <Sidebar collapsible="offcanvas" {...props}>
            <SidebarHeader>
                {/*<SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            asChild
                            className="data-[slot=sidebar-menu-button]:!p-1.5"
                        >
                            <a href="#">
                                <IconInnerShadowTop className="!size-5" />
                                <span className="text-base font-semibold">Acme Inc.</span>
                            </a>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>*/}
                {/*<AppTitle />*/}
                <TeamSwitcher teams={appSidebarData.teams} />
            </SidebarHeader>
            <SidebarContent>
                <NavMain items={navigationData?.navMain as any[]} />
            </SidebarContent>
            <SidebarFooter>
                <NavUser />
            </SidebarFooter>
        </Sidebar>
    );
}
