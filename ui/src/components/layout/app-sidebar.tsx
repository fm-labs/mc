import * as React from "react";

import { NavMain } from "@/components/layout/nav-main.tsx";
import { NavUser } from "@/components/layout/nav-user.tsx";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
} from "@/components/ui/sidebar.tsx";
import {appNavigationData, appSidebarData} from "@/components/layout/data/app-navigation-data.ts";
import { EnvironmentSwitcher } from "@/components/layout/environment-switcher.tsx";


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
                <EnvironmentSwitcher environments={appSidebarData.environments} />
            </SidebarHeader>
            <SidebarContent>
                <NavMain items={appNavigationData?.navMain as any[]} />
                {/*<NavFindings items={navigationData?.navFindings} />*/}
                {/*<NavSecondary items={appNavigationData?.navSecondary as any[]} className="mt-auto" />*/}
            </SidebarContent>
            <SidebarFooter>
                <NavUser />
            </SidebarFooter>
        </Sidebar>
    );
}
