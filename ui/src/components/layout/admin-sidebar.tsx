import * as React from "react";

import {NavSecondary} from "@/components/layout/nav-secondary.tsx";
import {NavUser} from "@/components/layout/nav-user.tsx";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
} from "@/components/ui/sidebar.tsx";
import {appSidebarData} from "@/components/layout/data/app-navigation-data.ts";
import {EnvironmentSwitcher} from "@/components/layout/environment-switcher.tsx";

import {adminNavigationData} from "@/components/layout/data/admin-navigation-data.ts";

export function AdminSidebar({...props}: React.ComponentProps<typeof Sidebar>) {
    // const {api} = useApi()
    // const [inventoryNavData, setInventoryNavData] = React.useState<NavigationItem[] | null>(null);
    //
    // const fetchInventoryMetadata = React.useCallback(async (): Promise<InventoryMetadata[]> => {
    //     try {
    //         const response = await api.get("/api/inventory");
    //         console.log("response", response);
    //         return response;
    //     } catch (error) {
    //         console.error("Error fetching inventory metadata:", error);
    //         throw error;
    //     }
    // }, [api]);
    //
    // const fetchAppNavigationData = React.useCallback(async () => {
    //     try {
    //         const metadata = await fetchInventoryMetadata()
    //         // map metadata to navigation data
    //         const navigation: NavigationItem[] = metadata ? metadata.map((item) => ({
    //             title: item.title,
    //             url: `/admin/inventory/${item.item_type}`,
    //             iconName: item?.item_type,
    //         })) : [];
    //         setInventoryNavData(navigation);
    //         return navigation;
    //     } catch (error) {
    //         console.error("Error fetching app navigation data:", error);
    //         return null;
    //     }
    // }, [fetchInventoryMetadata, setInventoryNavData]);
    //
    // React.useEffect(() => {
    //     fetchAppNavigationData();
    // }, [fetchAppNavigationData]);

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
                <EnvironmentSwitcher environments={appSidebarData.environments}/>
                <NavSecondary items={adminNavigationData?.navAdmin as any[]} className="mt-auto"/>
            </SidebarHeader>
            <SidebarContent>
                {/*<NavInventory items={inventoryNavData as any[]}/>*/}
                {/*<NavSecondary items={appNavigationData?.navAdmin as any[]} className="mt-auto"/>*/}
            </SidebarContent>
            <SidebarFooter>
                <NavUser/>
            </SidebarFooter>
        </Sidebar>
    );
}
