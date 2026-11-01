import {ContainerHostProvider, useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DockerHostError} from "@/app/containers/components/docker-host-error.tsx";
import DockerHostContainers from "@/app/containers/components/docker-host-containers.tsx";
import {useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";

const DockerHostsKitchensinkItem = ({host}: { host: any }) => {
    //const {summary} = useContainerHost();

    return (<li
        className="rounded-lg border p-1 mb-4 hover:shadow-md"
    >
        {/*<div className="mb-4 flex items-center justify-between">*/}
        {/*    <div className={"flex flex-row gap-x-4 items-start"}>*/}
        {/*        <div*/}
        {/*            className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}*/}
        {/*        >*/}
        {/*            <AppIcon size={24} icon={"docker"}/>*/}
        {/*        </div>*/}
        {/*        <div className={"mb-1"}>*/}
        {/*            <h2 className="font-semibold">{host.name}</h2>*/}
        {/*            <p className="line-clamp-2 text-gray-500">{host.properties.url}</p>*/}
        {/*        </div>*/}
        {/*    </div>*/}
        {/*    <div className={"flex flex-row gap-x-4 items-end"}>*/}
        {/*        <DockerHostSummary/>*/}
        {/*        <Button asChild variant={"outline"}>*/}
        {/*            <div>*/}
        {/*                <DockerHostStatus/>*/}
        {/*                <Link to={`${host.name}`}>{summary ? "Connected" : "Disconnected"}</Link>*/}
        {/*            </div>*/}
        {/*        </Button>*/}
        {/*    </div>*/}
        {/*</div>*/}
        <DockerHostError/>
        <DockerHostContainers/>
    </li>);
};


const DockerHostsKitchensink = () => {
    const {hosts} = useContainerHosts();

    return (
        <div>
            <ul className="faded-bottom no-scrollbar grid gap-2 overflow-auto">
                {hosts && hosts.length > 0 && hosts.map((host) => (
                    <ContainerHostProvider key={host.id} host={host}>
                        <DockerHostsKitchensinkItem host={host}/>
                    </ContainerHostProvider>
                ))}
            </ul>
        </div>
    );
};

export default DockerHostsKitchensink;
