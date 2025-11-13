import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import {useParams} from "react-router";
import {ContainerHostProvider} from "@/app/containers/components/container-host-provider.tsx";
import DockerHostContainers from "@/app/containers/components/docker-host-containers.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import {ContainerHostsProvider} from "@/app/containers/components/container-hosts-provider.tsx";
import DockerHostImages from "@/app/containers/components/docker-host-images.tsx";
import DockerHostVolumes from "@/app/containers/components/docker-host-volumes.tsx";


const ContainerHostPage = () => {
    const {hostId, view} = useParams<{ hostId: string, view: string }>();
    if (!hostId) {
        return <div>Host ID missing</div>
    }

    return (
        <ContainerHostsProvider>
            <ContainersLayout>
                <MainContent>
                    <ContainerHostProvider config={{hostId}}>
                        <DockerHostHeader subtitle={view}/>
                        {!view || view === "container" && <DockerHostContainers/>}
                        {view === "images" && <DockerHostImages/>}
                        {view === "volumes" && <DockerHostVolumes/>}
                    </ContainerHostProvider>
                </MainContent>
            </ContainersLayout>
        </ContainerHostsProvider>
    );
};

export default ContainerHostPage;
