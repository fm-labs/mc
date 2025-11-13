import React from "react";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import { DockerContainerProvider } from "@/app/containers/components/docker-container-provider.tsx";
import { DockerHostContainersListItem } from "@/app/containers/components/docker-host-containers.tsx";

const ContainerView = ({ containerId }: {containerId: string}) => {
    const { containers } = useContainerHost();

    const container = React.useMemo(() => {
        if (!containers) {
            return null;
        }
        return containers.find((c: any) => c.Id === containerId);
    }, [containers, containerId]);

    if (!container) {
        return <div>Loading container...</div>;
    }

    return (
        <DockerContainerProvider container={container}>
            <DockerHostContainersListItem open={true} />
        </DockerContainerProvider>
    );
};

export default ContainerView;
