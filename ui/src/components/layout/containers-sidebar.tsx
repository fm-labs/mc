import * as React from "react"
import {GalleryVerticalEnd, Minus, PlugIcon, PlugZap, PlugZapIcon, Plus} from "lucide-react"

import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
    Sidebar,
    SidebarContent,
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
import {NavLink} from "react-router";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";

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

export function ContainersSidebar({...props}: React.ComponentProps<typeof Sidebar>) {
    const {hosts} = useContainerHosts()

    const navContainers: ContainerNavItem[] = React.useMemo(() => {
        const items: ContainerNavItem[] = hosts.map((host) => ({
            title: host.id || host.id,
            isActive: false,
            isConnected: host?.connected,
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
                    title: "Events",
                    url: `/containers/${host.id}/events`,
                    icon: "container-events"
                },
            ],
        }))

        if (items.length > 0) {
            items[0].isActive = true
        }
        return items
    }, [hosts])

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
                                        <SidebarMenuButton>
                                            <div className={"flex items-center gap-2"}>
                                                <AppIcon icon={item?.icon}/>
                                                {item.title}{" "}
                                                {item?.isConnected &&
                                                    <span className={"text-green-500"} title={"Connected"}><PlugZapIcon size={"1em"} /></span>}
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
            </SidebarContent>
            <SidebarRail/>
        </Sidebar>
    )
}
