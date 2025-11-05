import {
    IconDiscord,
    IconDocker,
    IconFacebook,
    IconFigma,
    IconGithub,
    IconGitlab, IconGmail, IconMedium, IconNotion, IconSkype, IconSlack, IconStripe, IconTelegram, IconTrello,
    IconWhatsapp,
    IconZoom,
} from "@/assets/brand-icons";
import { IconJenkins } from "@/assets/brand-icons/icon-jenkins.tsx";
import {
    IconBook,
    IconClock,
    IconPlayerPause,
    IconPlayerPlay,
    IconPlayerSkipBack,
    IconPlayerStop,
    IconTrash,
    IconCamera,
    IconCloud,
    IconContainer,
    IconDashboard,
    IconFileAi,
    IconFileDescription,
    IconGlobe,
    IconHelp,
    IconListDetails,
    IconSearch,
    IconSettings,
    IconTool,
    IconUsers, IconSkull,
    IconTrendingDown, IconTrendingUp, IconNetwork, IconReport, IconWebhook, IconWorldDollar, IconWorld, IconCube,
    IconDatabase, IconCube3dSphere, IconCubeOff, IconCubeSpark,
} from "@tabler/icons-react";
import { type SVGProps } from "react";
import { IconPodman } from "@/assets/brand-icons/icon-podman.tsx";
import { HatGlassesIcon, Share2Icon } from "lucide-react";

const appIconsMap: {[key: string]: any} = {
    // navigation
    "dashboard": IconDashboard,
    "findings": HatGlassesIcon,
    "tool": IconTool,
    "kitchensink": IconTool,
    "integrations": IconTool,
    "cloud": IconCloud,
    "cube": IconCube,
    "cube-filled": IconCubeSpark,
    "container": IconCube,
    "database": IconDatabase,
    "inventory": IconListDetails,
    "network": Share2Icon,
    "search": IconSearch,
    "settings": IconSettings,
    "help": IconHelp,
    "profile": IconUsers,
    "users": IconUsers,
    "ai": IconFileAi,
    "docs": IconFileDescription,
    "documentation": IconFileDescription,
    "website": IconWebhook,
    "webcam": IconCamera,
    "application": IconDashboard,
    "apps": IconDashboard,
    "tasks": IconListDetails,
    "report": IconReport,
    "domain": IconWorld,

    // brands
    "discord": IconDiscord,
    "docker": IconDocker,
    "podman": IconPodman,
    "facebook": IconFacebook,
    "figma": IconFigma,
    "github": IconGithub,
    "gitlab":IconGitlab,
    "gmail": IconGmail,
    "medium": IconMedium,
    "notion": IconNotion,
    "skype": IconSkype,
    "slack": IconSlack,
    "stripe": IconStripe,
    "telegram": IconTelegram,
    "trello": IconTrello,
    "whatsapp": IconWhatsapp,
    "zoom": IconZoom,
    "jenkins": IconJenkins,
    "aws": IconCloud,
    // control icons
    "play": IconPlayerPlay,
    "start": IconPlayerPlay,
    "pause": IconPlayerPause,
    "stop": IconPlayerStop,
    "restart": IconPlayerSkipBack,
    "delete": IconTrash,
    // named icons
    "clock": IconClock,
    "book": IconBook,
    "globe": IconGlobe,
    "console": IconSkull,
    "trend-up": IconTrendingUp,
    "trend-down": IconTrendingDown,
    // inventory
    "repository": IconBook,
    "host": IconCloud,
    "host-network": IconNetwork,
    "container-host": IconDocker,
    "container-image": IconCube3dSphere,
    "container-volume": IconDatabase,
    "dns-domain": IconGlobe,
    "compose-project": IconDashboard,
    "docker-mcp": IconDocker,
    "xterm": IconTool,
    "orchestra": IconTool,
    "ansible": IconTool,
    "jobs": IconClock,
    "chats": IconSlack,
};

const IconDefault = ({ className, ...props }: SVGProps<SVGSVGElement>) => {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} {...props}>
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
            <path d="M8 12L11 15L16 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
    )
};

export const getIconByName = (name: string) => {
    let key: string = name.toLowerCase();
    if (key.startsWith("app:")) {
        key = key.substring(4);
    }
    return appIconsMap[key] || IconDefault;
};

export default appIconsMap;
