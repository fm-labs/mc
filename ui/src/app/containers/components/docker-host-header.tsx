import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import Header from "@/components/header.tsx";
import React, {PropsWithChildren} from "react";

const DockerHostHeader = ({title, children}: PropsWithChildren<{ title?: string }>) => {
    const {config, info} = useContainerHost()

    const infoText = React.useMemo(() => {
        return info ? `${info.Containers} Container (${info.ContainersRunning} running, ${info.ContainersPaused} paused, ${info.ContainersStopped} stopped) | ${info.Images} Images` : '';
    }, [info])


    return (
        <Header title={`${config.hostId} : ${title}`} subtitle={infoText}>{children}</Header>
    );
};

export default DockerHostHeader;
