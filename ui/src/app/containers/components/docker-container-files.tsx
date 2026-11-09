import React from 'react';
import {useDockerContainer} from "@/app/containers/components/docker-container-provider.tsx";

const DockerContainerFiles = () => {
    const { container } = useDockerContainer()
    return (
        <div>
            <h1>Files</h1>
        </div>
    );
};

export default DockerContainerFiles;