export type NavigationItem = {
    title: string;
    url: string;
    icon?: React.ComponentType<any>;
    iconName?: string;
    isActive?: boolean;
    items?: NavigationItem[];
};
export type AppNavigationData = {
    //user: any,
    navMain: NavigationItem[];
    navSecondary: NavigationItem[];
    navFindings: NavigationItem[];
    navContainers: NavigationItem[];
    navAdmin: NavigationItem[];
    navInventory: NavigationItem[];
}
