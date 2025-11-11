import { ShieldIcon, UserCog, UserIcon, Wrench } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import MainContent from "@/components/layout/main-content.tsx";
import { Outlet } from "react-router";
import { SettingsNav } from "@/app/settings/components/settings-nav.tsx";
import { FEAT_SETTINGS_ENABLED } from "@/constants.ts";
import {IconPigMoney} from "@tabler/icons-react";

const sidebarNavItems = [
    // {
    //     title: "Profile",
    //     href: "/settings/profile",
    //     icon: <UserCog size={18} />,
    // },
    {
        title: "Account",
        href: "/settings/account",
        icon: <UserIcon size={18} />,
    },
    {
        title: "Security",
        href: "/settings/security",
        icon: <ShieldIcon size={18} />,
    },
    {
        title: "Credits",
        href: "/settings/credits",
        icon: <IconPigMoney size={18} />,
    },
    // {
    //   title: 'Appearance',
    //   href: '/settings/appearance',
    //   icon: <Palette size={18} />,
    // },
    // {
    //   title: 'Notifications',
    //   href: '/settings/notifications',
    //   icon: <Bell size={18} />,
    // },
    // {
    //   title: 'Display',
    //   href: '/settings/display',
    //   icon: <Monitor size={18} />,
    // },
];

export function SettingsPage() {
    if (!FEAT_SETTINGS_ENABLED) {
        return <div className={"p-4"}>Settings feature is disabled.</div>;
    }

    return (
        <>
            <MainContent>
                <div className="space-y-0.5">
                    <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
                        Settings
                    </h1>
                    <p className="text-muted-foreground">
                        Manage your account settings and set e-mail preferences.
                    </p>
                </div>
                <Separator className="my-4 lg:my-6" />
                <div
                    className="flex flex-1 flex-col space-y-2 overflow-hidden md:space-y-2 lg:flex-row lg:space-y-0 lg:space-x-12">
                    <aside className="top-0 lg:sticky lg:w-1/5">
                        <SettingsNav items={sidebarNavItems} />
                    </aside>
                    <div className="flex w-full overflow-y-hidden p-1">
                        <Outlet />
                    </div>
                </div>
            </MainContent>
        </>
    );
}
