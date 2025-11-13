import { Outlet } from "react-router";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar.tsx";
import { SiteHeader } from "@/components/layout/site-header.tsx";
import React, { PropsWithChildren } from "react";
import {ContainersSidebar} from "@/components/layout/containers-sidebar.tsx";

const ContainersLayout = (props: PropsWithChildren) => {
    return (
        <>
            <SidebarProvider
                defaultOpen={true}
                style={
                    {
                        "--sidebar-width": "calc(var(--spacing) * 72)",
                        "--header-height": "calc(var(--spacing) * 12)",
                    } as React.CSSProperties
                }
            >
                <ContainersSidebar variant="inset" />
                <SidebarInset>
                    <SiteHeader />
                    <div className="flex flex-1 flex-col">
                        <div className="@container/main flex flex-1 flex-col gap-2">
                            {props?.children || <Outlet />}
                        </div>
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </>
    );
};

export default ContainersLayout;
