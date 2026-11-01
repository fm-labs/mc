import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import {useParams} from "react-router";
import {ContainerHostProvider, useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import DockerHostContainers from "@/app/containers/components/docker-host-containers.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import {ContainerHostsProvider, useContainerHosts} from "@/app/containers/components/container-hosts-provider.tsx";
import DockerHostImages from "@/app/containers/components/docker-host-images.tsx";
import DockerHostVolumes from "@/app/containers/components/docker-host-volumes.tsx";
import DockerHostNetworks from "@/app/containers/components/docker-host-networks.tsx";
import DockerHostEvents from "@/app/containers/components/docker-host-events.tsx";
import {DockerHostError} from "@/app/containers/components/docker-host-error.tsx";
import DockerHostEngine from "@/app/containers/components/docker-host-engine.tsx";
import {Button} from "@/components/ui/button";

const VIEW_HEADERS: Record<string, { title: string, icon: string }> = {
    container: {title: "Containers", icon: "container"},
    images: {title: "Images", icon: "container-image"},
    volumes: {title: "Volumes", icon: "container-volume"},
    networks: {title: "Networks", icon: "container-network"},
    engine: {title: "Engine", icon: "info"},
    events: {title: "Events", icon: "container-events"},
};

// Shown instead of the view while the host is disconnected
const ContainerHostDisconnected = ({view}: { view?: string }) => {
    const {setEnabled} = useContainerHost();
    const header = VIEW_HEADERS[view || "container"] ?? VIEW_HEADERS.container;
    return (
        <>
            <DockerHostHeader title={header.title} icon={header.icon}/>
            <div className="rounded-lg border border-dashed px-4 py-10 text-center">
                <p className="text-muted-foreground">This host is disconnected. No data is fetched while it is off.</p>
                <Button className="mt-3" onClick={() => setEnabled(true)}>Connect</Button>
            </div>
        </>
    );
};

const ContainerHost = ({hostId, view}: {hostId: string, view?: string}) => {
    const {hosts} = useContainerHosts()
    const host = hosts.find(h => h.id === hostId);
    if (!host) {
        return <div>Host not found: {hostId}</div>;
    }

    return <div>
        <ContainerHostProvider host={host} hideDisconnectButton
                               disabledFallback={<ContainerHostDisconnected view={view}/>}>
            <DockerHostError />
            {!view || view === "container" && <DockerHostContainers/>}
            {view === "images" && <DockerHostImages/>}
            {view === "volumes" && <DockerHostVolumes/>}
            {view === "networks" && <DockerHostNetworks/>}
            {view === "engine" && <DockerHostEngine />}
            {view === "events" && <DockerHostEvents/>}
        </ContainerHostProvider>
    </div>;
}

const ContainerHostPage = () => {
    const {hostId, view} = useParams<{ hostId: string, view: string }>();
    if (!hostId) {
        return <div>Host ID missing</div>
    }

    return (
        <ContainerHostsProvider>
            <ContainersLayout>
                <MainContent>
                    <ContainerHost hostId={hostId} view={view} />
                </MainContent>
            </ContainersLayout>
        </ContainerHostsProvider>
    );
};

export default ContainerHostPage;
