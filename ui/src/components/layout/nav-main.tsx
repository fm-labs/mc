import { IconCirclePlusFilled, IconSparkles } from "@tabler/icons-react";

import { Button } from "@/components/ui/button.tsx";
import {
    SidebarGroup,
    SidebarGroupContent,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar.tsx";
import { NavLink } from "react-router";
import AppIcon from "@/components/app-icon.tsx";

import { NavigationItem } from "@/components/layout/data/types.ts";
import useDialog from "@/hooks/use-dialog.tsx";
import React, { ReactPortal } from "react";
import QuickCreateForm from "@/components/quick-create-form.tsx";

export function NavMain({
                            items,
                        }: {
    items: NavigationItem[]
}) {
    const { createDialog } = useDialog();
    const [portal, setPortal] = React.useState<ReactPortal | null>(null);

    const handleQuickCreate = () => {
        console.log("Quick Create clicked");

        const content = <QuickCreateForm />;

        const p = createDialog({
            title: "Quick Create",
            children: content,
            onClose: () => setPortal(null),
            size: "md",
        });
        setPortal(p);
    };

    return (<>
            <SidebarGroup>
                <SidebarGroupContent className="flex flex-col gap-2">
                    {/*<SidebarMenu>
                        <SidebarMenuItem className="flex items-center gap-2">
                            <SidebarMenuButton
                                tooltip="Quick Create"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground min-w-8 duration-200 ease-linear"
                                onClick={handleQuickCreate}
                            >
                                <IconCirclePlusFilled />
                                <span>Quick Create</span>
                            </SidebarMenuButton>
                            <Button
                                size="icon"
                                className="size-8 group-data-[collapsible=icon]:opacity-0"
                                variant="outline"
                                title={"Open AI Assistant"}
                            >
                                <IconSparkles />
                                <span className="sr-only">Assistant</span>
                            </Button>
                        </SidebarMenuItem>
                    </SidebarMenu>*/}
                    <SidebarMenu>
                        {items && items.map((item) => (
                            <SidebarMenuItem key={item.title}>
                                <SidebarMenuButton tooltip={item.title}>
                                    <AppIcon icon={item?.iconName} />
                                    <NavLink to={item.url}>{item.title}</NavLink>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        ))}
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
            {portal}
        </>
    );
}
