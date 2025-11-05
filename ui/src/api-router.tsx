import React from "react";
import { useApi } from "@/context/api-context.tsx";
import { createBrowserRouter, RouteObject, RouterProvider } from "react-router";
import Root from "@/app/root.tsx";
import AuthLayout from "@/components/layout/auth-layout.tsx";
import AdminLayout from "@/components/layout/admin-layout.tsx";
import MainLayout from "@/components/layout/main-layout.tsx";
import { NotFoundError } from "@/features/errors/not-found-error.tsx";
import AuthenticatedRoute from "@/components/authenticated-route.tsx";

// lazy load pages
const InventoryPage = await import('@/app/inventory/page.tsx').then(mod => mod.default);
const XtermPage = await import('@/developer/xterm/page.tsx').then(mod => mod.default);
const FindingsPage = await import('@/app/findings/page.tsx').then(mod => mod.default);
const McpServersPage = await import('@/app/mcp-servers/page.tsx').then(mod => mod.default);
const DockerMcpCatalogPage = await import('@/app/mcp-servers/docker-catalog-page.tsx').then(mod => mod.default);
const OrchestraJobsPage = await import('@/app/ansible/page.tsx').then(mod => mod.default);
const ToolsPage = await import('@/app/tools/page.tsx').then(mod => mod.default);
const TasksPage = await import('@/app/tasks/page.tsx').then(mod => mod.default);
const ChatsPage = await import('@/app/chats/page.tsx').then(mod => mod.ChatsPage);
const ContainerHostsPage = await import('@/app/containers/container-hosts-page.tsx').then(mod => mod.default);
const ContainerHostPage = await import('@/app/containers/container-host-page.tsx').then(mod => mod.default);
const ContainerPage = await import('@/app/containers/container-page.tsx').then(mod => mod.default);
const AwsInventoryPage = await import('@/app/aws/aws-inventory-page.tsx').then(mod => mod.default);
const AwsNetworksPage = await import('@/app/aws/aws-networks-page.tsx').then(mod => mod.default);
const NetworksPage = await import('@/app/infrastructure/networks-page.tsx').then(mod => mod.default);
const HostPage = await import('@/app/infrastructure/host-page.tsx').then(mod => mod.default);
const DomainsPage = await import('@/app/inventory/dns-domain/page.tsx').then(mod => mod.default);
const WebcheckPage = await import('@/app/inventory/dns-domain/webcheck-page.tsx').then(mod => mod.default);
const IntegrationsPage = await import('@/app/integrations/page.tsx').then(mod => mod.IntegrationsPage);
const SettingsPage = await import('@/app/settings/page.tsx').then(mod => mod.SettingsPage);
const SettingsProfile = await import('@/app/settings/profile').then(mod => mod.SettingsProfile);
const SettingsAccount = await import('@/app/settings/account').then(mod => mod.SettingsAccount);
const SettingsSecurity = await import('@/app/settings/security').then(mod => mod.SettingsSecurity);
const WelcomePage = await import('@/app/welcome/welcome-page.tsx').then(mod => mod.default);
const LoginPage = await import('@/app/auth/login-page.tsx').then(mod => mod.default);
const GithubLoginPage = await import('@/app/auth/github-login-page.tsx').then(mod => mod.default);
const RegisterPage = await import('@/app/auth/register-page.tsx').then(mod => mod.default);
const DashboardPage = await import('@/app/dashboard/page.tsx').then(mod => mod.default);
const KitchensinkPage = await import('@/app/kitchensink/page.tsx').then(mod => mod.default);

const ApiRouter = () => {
    const { api: apiClient } = useApi()

    const routes: RouteObject[] = [
        {
            path: "/",
            Component: Root,
            children: [
                { index: true, Component: WelcomePage },
                {
                    path: "auth",
                    Component: AuthLayout,
                    children: [
                        { path: "login", Component: LoginPage },
                        { path: "register", Component: RegisterPage },
                        { path: "callback/github", Component: GithubLoginPage },
                    ],
                },
                {
                    Component: AuthenticatedRoute,
                    children: [
                        {
                            path: "dashboard",
                            Component: MainLayout,
                            children: [
                                {
                                    index: true,
                                    Component: DashboardPage,
                                }
                            ]
                        },
                        {
                            path: "findings", // secops
                            Component: MainLayout,
                            children: [
                                {
                                    index: true,
                                    Component: FindingsPage,
                                }
                            ]
                        },
                        {
                            path: "mcp-servers",
                            Component: MainLayout,
                            children: [
                                {
                                    index: true,
                                    Component: McpServersPage,
                                },
                                {
                                    path: "docker",
                                    Component: DockerMcpCatalogPage,
                                }
                            ]
                        },
                        {
                            path: "ai", // ai
                            Component: ChatsPage,
                        },
                        {
                            path: "infrastructure", // devops
                            Component: MainLayout,
                            children: [
                                {
                                    index: true,
                                    Component: NetworksPage,
                                    loader: () => {
                                        return apiClient.getInventoryItems("host-network");
                                    },
                                },
                                {
                                    path: "host/:hostId",
                                    Component: HostPage,
                                    loader: ({ params }) => {
                                        const { hostId } = params;
                                        if (hostId) {
                                            return apiClient.getInventoryItem("host", hostId);
                                        }
                                    },
                                },
                                {
                                    path: "domains",
                                    children: [
                                        {
                                            index: true,
                                            Component: DomainsPage,
                                            loader: () => {
                                                return apiClient.getInventoryItems("dns-domain");
                                            },
                                        },
                                        {
                                            path: "webcheck",
                                            children: [{
                                                path: ":domain",
                                                Component: WebcheckPage,
                                            }]
                                        }
                                    ]
                                },
                                {
                                    path: "aws",
                                    children: [
                                        {
                                            index: true,
                                            Component: AwsInventoryPage
                                        },
                                        {
                                            path: "networks",
                                            Component: AwsNetworksPage
                                        }
                                    ]
                                },
                            ]
                        },
                        {
                            path: "containers", // docker/containers
                            //Component: ContainersLayout,
                            children: [
                                {
                                    index: true,
                                    Component: ContainerHostsPage,
                                },
                                {
                                    path: ":hostId",
                                    Component: ContainerHostPage,
                                },
                                {
                                    path: ":hostId/container/:containerId",
                                    Component: ContainerPage,
                                }
                            ],
                        },
                        // {
                        //     path: "settings/:section",
                        //     Component: SettingsPage,
                        // },
                        {
                            path: "settings",
                            Component: SettingsPage,
                            children: [
                                { path: "profile", Component: SettingsProfile },
                                { path: "account", Component: SettingsAccount },
                                { path: "security", Component: SettingsSecurity },
                            ]
                        },
                        {
                            path: "admin", // admin tools
                            Component: AdminLayout,
                            children: [
                                {
                                    //path: "kitchensink",
                                    index: true,
                                    Component: KitchensinkPage,
                                },
                                {
                                    path: "ansible",
                                    Component: OrchestraJobsPage,
                                },
                                {
                                    path: "xterm",
                                    Component: XtermPage,
                                },
                                {
                                    path: "integrations",
                                    Component: IntegrationsPage,
                                },
                                {
                                    path: "tasks",
                                    Component: TasksPage,
                                },
                                {
                                    path: "tools",
                                    Component: ToolsPage,
                                    loader: () => {
                                        return apiClient.getToolList();
                                    },
                                },
                                {
                                    path: "inventory",
                                    children: [
                                        // {
                                        //     path: "apps",
                                        //     Component: InventoryPage,
                                        //     loader: () => {
                                        //         return apiClient.getInventoryItems("compose-app");
                                        //     },
                                        // },
                                        {
                                            path: ":itemType",
                                            Component: InventoryPage,
                                            loader: ({ params }) => {
                                                const { itemType } = params;
                                                if (itemType) {
                                                    return apiClient.getInventoryItems(itemType);
                                                }
                                            },
                                        },
                                    ],
                                },
                            ]
                        },
                    ],
                },
                {
                    "path": "*",
                    Component: NotFoundError,
                }
            ],
        },
    ];

    const router = React.useMemo(() => {
        return createBrowserRouter(routes);
    }, []);

    return <RouterProvider router={router} />
};

export default ApiRouter;
