import {LOCAL_NODE} from "@/lib/node-headers.ts";
import * as React from "react"
import {Minus, MoreHorizontal, Plus, Power} from "lucide-react"

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
    SidebarRail, useSidebar,
} from "@/components/ui/sidebar"
import AppIcon from "@/components/app-icon.tsx";
import {NavLink, useNavigate} from "react-router";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import {NavUser} from "@/components/layout/nav-user.tsx";
import {appNavigationData, appSidebarData} from "@/components/layout/data/app-navigation-data.ts";
import {NavSecondary} from "@/components/layout/nav-secondary.tsx";
import {EnvironmentSwitcher} from "@/components/layout/environment-switcher.tsx";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu.tsx";
import {HostStatusDot, hostStatusTitle} from "@/app/containers/components/host-status.tsx";

type NavItem = {
    title: string
    url: string
    isActive?: boolean
    icon?: React.ReactNode | string
    items?: NavItem[]
}

type ContainerNavItem = NavItem & {
    hostId: string
    isEnabled: boolean
    secondaryItems?: NavItem[]
}

// Icon color for enabled hosts, per engine
const ENGINE_COLORS: Record<string, string> = {
    "docker": "text-[#2496ED]",
    "container-host": "text-[#2496ED]",
    "podman": "text-[#892CA0] dark:text-[#B36BD1]",
    "node": "text-emerald-600 dark:text-emerald-400",
}
const engineColor = (icon?: React.ReactNode | string) =>
    (typeof icon === "string" && ENGINE_COLORS[icon]) || "text-green-600 dark:text-green-400"

const isMcHost = (host: { id: string, properties?: { engine?: string } }) =>
    host.id === LOCAL_NODE || host.properties?.engine === "node"

export function ContainersSidebar({...props}: React.ComponentProps<typeof Sidebar>) {
    const {hosts, isHostEnabled, setHostEnabledState, getHostStatus} = useContainerHosts()
    const navigate = useNavigate()

    const navContainers: ContainerNavItem[] = React.useMemo(() => {

        const items: ContainerNavItem[] = hosts.map((host) => {

            return {
                title: host.id,
                hostId: host.id,
                isActive: false,
                isEnabled: isHostEnabled(host.id),
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
                // these pages only exist on an mc: this one, or a node reached via the node proxy
                secondaryItems: [
                    ...(isMcHost(host) ? [
                        {
                            title: "Tools",
                            url: `/manage/${host.id}/tools`,
                            icon: "tool"
                        },
                        {
                            title: "RPC",
                            url: `/manage/${host.id}/rpc`,
                            icon: "settings"
                        },
                        {
                            title: "Apps",
                            url: `/manage/${host.id}/apps`,
                            icon: "apps"
                        },
                        {
                            title: "Settings",
                            url: `/manage/${host.id}/settings`,
                            icon: "settings"
                        },
                    ] : [])
                ]
            }
        })

        if (items.length > 0) {
            items[0].isActive = true
        }
        return items
    }, [hosts, isHostEnabled])

    const {isMobile} = useSidebar()

    return (
        <Sidebar {...props}>
            <SidebarHeader>
                {/*<SidebarMenu>*/}
                {/*    <SidebarMenuItem>*/}
                {/*        <SidebarMenuButton size="lg" asChild>*/}
                {/*            <a href="#">*/}
                {/*                <div*/}
                {/*                    className="bg-sidebar-accent text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">*/}
                {/*                    <AppIcon icon={"container"} className="size-4"/>*/}
                {/*                </div>*/}
                {/*                <div className="flex flex-col gap-0.5 leading-none">*/}
                {/*                    <span className="font-medium">Containers</span>*/}
                {/*                    <span className="">v1.0.0</span>*/}
                {/*                </div>*/}
                {/*            </a>*/}
                {/*        </SidebarMenuButton>*/}
                {/*    </SidebarMenuItem>*/}
                {/*</SidebarMenu>*/}
                {/*<SearchForm />*/}

                <EnvironmentSwitcher environments={appSidebarData.environments}/>
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
                                <NavLink to={"/containers/stats"}>Dashboard</NavLink>
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
                                    <SidebarMenuButton>
                                        <CollapsibleTrigger asChild>
                                            <div
                                                onClick={() => navigate(item.url + '/container')}
                                                className={`flex min-w-0 items-center gap-2 ${item.isEnabled ? "" : "text-muted-foreground"}`}
                                                title={hostStatusTitle({enabled: item.isEnabled, ...getHostStatus(item.hostId)})}>
                                                <AppIcon icon={item?.icon}
                                                         className={`shrink-0 ${item.isEnabled ? engineColor(item.icon) : "opacity-60"}`}/>
                                                <span
                                                    className={`truncate ${item.isEnabled ? "font-medium" : "line-through decoration-muted-foreground/40"}`}>{item.title}</span>
                                                <HostStatusDot hostId={item.hostId}/>
                                            </div>
                                        </CollapsibleTrigger>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <MoreHorizontal className="ml-auto"/>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent
                                                side={isMobile ? "bottom" : "right"}
                                                align={isMobile ? "end" : "start"}
                                                className="min-w-56 rounded-lg"
                                            >
                                                <DropdownMenuItem onSelect={() => setHostEnabledState(item.hostId, !item.isEnabled)}>
                                                    <Power/>
                                                    {item.isEnabled ? "Disable host" : "Enable host"}
                                                </DropdownMenuItem>
                                                {item.secondaryItems?.length ? <DropdownMenuSeparator/> : null}
                                                {item.secondaryItems?.map((sec) => <DropdownMenuItem key={sec.url} asChild>
                                                    <NavLink to={sec.url}>
                                                        <AppIcon icon={sec?.icon}/>
                                                        {sec.title}
                                                    </NavLink>
                                                </DropdownMenuItem>)}
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </SidebarMenuButton>
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
                <NavSecondary items={appNavigationData?.navSecondary as any[]} className="mt-auto"/>
            </SidebarContent>
            <SidebarFooter>
                <NavUser/>
            </SidebarFooter>
            <SidebarRail/>
        </Sidebar>
    )
}
