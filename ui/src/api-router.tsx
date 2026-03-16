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
const ToolsPage = await import('@/app/tools/page.tsx').then(mod => mod.default);
const ContainerHostsPage = await import('@/app/containers/container-hosts-page.tsx').then(mod => mod.default);
const ContainerHostPage = await import('@/app/containers/container-host-page.tsx').then(mod => mod.default);
const ContainerPage = await import('@/app/containers/container-page.tsx').then(mod => mod.default);
const WelcomePage = await import('@/app/welcome/welcome-page.tsx').then(mod => mod.default);
const LoginPage = await import('@/app/auth/login-page.tsx').then(mod => mod.default);
const DashboardPage = await import('@/app/dashboard/page.tsx').then(mod => mod.default);
const KitchensinkPage = await import('@/app/kitchensink/page.tsx').then(mod => mod.default);
const PortainerTemplatesPage = await import('@/app/app-stacks/portainer-templates-page.tsx').then(mod => mod.default);
const AppStacksPage = await import('@/app/app-stacks/app-stacks-page.tsx').then(mod => mod.default);
const AppStackDetailsPage = await import('@/app/app-stacks/app-stack-details-page.tsx').then(mod => mod.default);
const RpcPage = await import('@/app/rpc/rpc-page.tsx').then(mod => mod.default);


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
                        //{ path: "callback/github", Component: GithubLoginPage },
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
                            path: "stacks", // secops
                            Component: MainLayout,
                            children: [
                                {
                                    index: true,
                                    Component: AppStacksPage,
                                    // loader: () => {
                                    //     return apiClient.getInventoryItems("app-stack");
                                    // },
                                },
                                {
                                    path: "details/:stackId",
                                    Component: AppStackDetailsPage,
                                    loader: ({ params }) => {
                                        return apiClient.getInventoryItem("app-stack", params.stackId!);
                                    },
                                },
                                {
                                    path: "portainer",
                                    Component: PortainerTemplatesPage,
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
                                    path: ":hostId/:view",
                                    Component: ContainerHostPage,
                                },
                                {
                                    path: ":hostId/container/:containerId",
                                    Component: ContainerPage,
                                }
                            ],
                        },
                        {
                            path: "admin", // admin tools
                            Component: AdminLayout,
                            children: [
                                {
                                    index: true,
                                    Component: KitchensinkPage,
                                },
                                // {
                                //     path: "tasks",
                                //     Component: TasksPage,
                                // },
                                {
                                    path: "rpc",
                                    Component: RpcPage,
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
