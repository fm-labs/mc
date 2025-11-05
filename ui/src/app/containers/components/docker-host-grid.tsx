import { Button } from "@/components/ui/button.tsx";
import { Link } from "react-router";
import AppIcon from "@/components/app-icon.tsx";
import { ContainerHostProvider, useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import { DockerHostStatus } from "@/app/containers/components/docker-host-status.tsx";
import { DockerHostError } from "@/app/containers/components/docker-host-error.tsx";
import { DockerHostSummary } from "@/app/containers/components/docker-host-summary.tsx";


export const DockerHostsGridItem = ({host}: {host: any}) => {
    const { summary } = useContainerHost()
    const engine = host.url.split("+", 1)[0]

    return (<li
        className="rounded-lg border p-4 hover:shadow-md"
    >
        <div className="mb-8 flex items-center justify-between">
            <div
                className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
            >
                <AppIcon size={24} icon={engine} />
            </div>
            <Button asChild variant={"outline"}>
                <div>
                    <DockerHostStatus />
                    <Link to={`${host.id}`}>{summary ? "Connected" : "Disconnected"}</Link>
                </div>
            </Button>
        </div>
        <div>
            <p className="line-clamp-2 text-gray-500">ID: {host.id}</p>
            <h2 className="mb-1 font-semibold">{host.url}</h2>
        </div>
        <DockerHostSummary />
        <DockerHostError />
    </li>)
}


export const DockerHostsGrid = ({hosts}: {hosts: any[]}) => {

    return (
        <div>
            <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 md:grid-cols-2 lg:grid-cols-3">
                {hosts && hosts.length > 0 && hosts.map((host) => (
                    <ContainerHostProvider config={{hostId: host.id}} key={host.id}>
                        <DockerHostsGridItem host={host} />
                    </ContainerHostProvider>
                ))}
            </ul>
        </div>
    );
};

export default DockerHostsGrid;
