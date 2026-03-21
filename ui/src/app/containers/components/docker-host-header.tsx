import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import Header from "@/components/header.tsx";
import {PropsWithChildren} from "react";

const DockerHostHeader = ({title, children}: PropsWithChildren<{ title?: string }>) => {
    const {config, info} = useContainerHost()

    const infoText = info ? `${info.Containers} Container (${info.ContainersRunning} running, ${info.ContainersPaused} paused, ${info.ContainersStopped} stopped) | ${info.Images} Images` : '';

    return (
        <Header title={`${config.hostId} : ${title}`} subtitle={infoText}>{children}</Header>
    );
};

export default DockerHostHeader;
