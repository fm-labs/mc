import * as React from "react"
import {Minus, Plus} from "lucide-react"

import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
    Sidebar,
    SidebarContent, SidebarFooter,
    SidebarGroup, SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSub,
    SidebarMenuSubItem,
    SidebarRail,
} from "@/components/ui/sidebar"
import AppIcon from "@/components/app-icon.tsx";
import {NavLink, useNavigate} from "react-router";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import {NavUser} from "@/components/layout/nav-user.tsx";
import {navigationData} from "@/components/layout/data/app-navigation-data.ts";
import {NavSecondary} from "@/components/layout/nav-secondary.tsx";

type NavItem = {
    title: string
    url: string
    isActive?: boolean
    icon?: React.ReactNode | string
    items?: NavItem[]
}

type ContainerNavItem = NavItem & {
    isConnected?: boolean
}

// Icon color for connected hosts, per engine
const ENGINE_COLORS: Record<string, string> = {
    "docker": "text-[#2496ED]",
    "container-host": "text-[#2496ED]",
    "podman": "text-[#892CA0] dark:text-[#B36BD1]",
    "node": "text-emerald-600 dark:text-emerald-400",
}
const engineColor = (icon?: React.ReactNode | string) =>
    (typeof icon === "string" && ENGINE_COLORS[icon]) || "text-green-600 dark:text-green-400"

export function ContainersSidebar({...props}: React.ComponentProps<typeof Sidebar>) {
    const {hosts, isHostEnabled} = useContainerHosts()
    const navigate = useNavigate()

    const navContainers: ContainerNavItem[] = React.useMemo(() => {

        const items: ContainerNavItem[] = hosts.map((host) => {

            return {
            title: host.id || host.id,
            isActive: false,
            isConnected: isHostEnabled(host.id),
            url: `/containers/${host.id}`,
            icon: host.properties?.engine || "container-host",
            items: [
                {
                    title: "Containers",
                    url: `/containers/${host.id}/container`,
                    icon: "container"
                },
                {
                    title: "Images",
                    url: `/containers/${host.id}/images`,
                    icon: "container-image"
                },
                {
                    title: "Volumes",
                    url: `/containers/${host.id}/volumes`,
                    icon: "container-volume"
                },
                {
                    title: "Networks",
                    url: `/containers/${host.id}/networks`,
                    icon: "container-network"
                },
                {
                    title: "Engine",
                    url: `/containers/${host.id}/engine`,
                    icon: "info"
                },
                {
                    title: "Events",
                    url: `/containers/${host.id}/events`,
                    icon: "container-events"
                },
            ],
        }
        })

        if (items.length > 0) {
            items[0].isActive = true
        }
        return items
    }, [hosts, isHostEnabled])

    return (
        <Sidebar {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <a href="#">
                                <div
                                    className="bg-sidebar-accent text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                                    <AppIcon icon={"container"} className="size-4"/>
                                </div>
                                <div className="flex flex-col gap-0.5 leading-none">
                                    <span className="font-medium">Containers</span>
                                    <span className="">v1.0.0</span>
                                </div>
                            </a>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
                {/*<SearchForm />*/}
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup className="group-data-[collapsible=icon]:hidden">
                    <SidebarMenu>
                        <SidebarMenuItem>
                            <SidebarMenuButton>
                                <AppIcon icon={"container"}/>
                                <NavLink to={"/containers"}>All containers</NavLink>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                        <SidebarMenuItem>
                            <SidebarMenuButton>
                                <AppIcon icon={"report"}/>
                                <NavLink to={"/containers/stats"}>Stats</NavLink>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                        <SidebarMenuItem>
                            <SidebarMenuButton>
                                <AppIcon icon={"container-network"}/>
                                <NavLink to={"/containers/network"}>Network</NavLink>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    </SidebarMenu>
                </SidebarGroup>
                <SidebarGroup>
                    <SidebarGroupLabel>Hosts</SidebarGroupLabel>
                    <SidebarMenu>
                        {navContainers.map((item, index) => (
                            <Collapsible
                                key={item.title}
                                defaultOpen={item?.isActive}
                                className="group/collapsible"
                            >
                                <SidebarMenuItem>
                                    <CollapsibleTrigger asChild>
                                        <SidebarMenuButton onClick={() => navigate(item.url + '/container')}>
                                            <div className={`flex min-w-0 items-center gap-2 ${item.isConnected ? "" : "text-muted-foreground"}`}
                                                 title={item.isConnected ? "Connected" : "Not connected"}>
                                                <AppIcon icon={item?.icon}
                                                         className={`shrink-0 ${item.isConnected ? engineColor(item.icon) : "opacity-60"}`}/>
                                                <span className={`truncate ${item.isConnected ? "font-medium" : ""}`}>{item.title}</span>
                                                {item.isConnected &&
                                                    <span className="size-1.5 shrink-0 rounded-full bg-green-500" aria-label="Connected"/>}
                                            </div>
                                            <Plus className="ml-auto group-data-[state=open]/collapsible:hidden"/>
                                            <Minus className="ml-auto group-data-[state=closed]/collapsible:hidden"/>
                                        </SidebarMenuButton>
                                    </CollapsibleTrigger>
                                    {item.items?.length ? (
                                        <CollapsibleContent>
                                            <SidebarMenuSub>
                                                {item.items.map((item) => (
                                                    <SidebarMenuSubItem key={item.title}>
                                                        <SidebarMenuButton tooltip={item.title}>
                                                            <AppIcon icon={item?.icon}/>
                                                            <NavLink to={item.url}>{item.title}</NavLink>
                                                        </SidebarMenuButton>
                                                    </SidebarMenuSubItem>
                                                ))}
                                            </SidebarMenuSub>
                                        </CollapsibleContent>
                                    ) : null}
                                </SidebarMenuItem>
                            </Collapsible>
                        ))}
                    </SidebarMenu>
                </SidebarGroup>
                <NavSecondary items={navigationData?.navAdmin as any[]} className="mt-auto"/>
            </SidebarContent>
            <SidebarFooter>
                <NavUser/>
            </SidebarFooter>
            <SidebarRail/>
        </Sidebar>
    )
}
