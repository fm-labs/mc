import { Outlet, useParams } from "react-router";
import { ContainerHostsProvider } from "@/app/containers/components/container-hosts-provider.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import { HostApiProvider } from "@/context/api-context.tsx";

/**
 * Layout for /manage/:hostId pages (tools, rpc, apps, settings).
 * Every useApi() call in these pages goes to the host from the URL. The sidebar sits outside
 * HostApiProvider, so it keeps loading the host list from the local mc.
 */
const ManageLayout = () => {
    const { hostId } = useParams<{ hostId: string }>();
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return (
        <ContainerHostsProvider>
            <ContainersLayout>
                {/* key drops page state when switching hosts */}
                <HostApiProvider key={hostId} hostId={hostId}>
                    <Outlet />
                </HostApiProvider>
            </ContainersLayout>
        </ContainerHostsProvider>
    );
};

export default ManageLayout;
