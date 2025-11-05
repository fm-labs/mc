import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import React from "react";
import ReactJson from "@microlink/react-json-view";

const DockerContainerEnvTable = () => {
    const { container } = useDockerContainer()

    return (
        <>
            <ReactJson src={container}
                       displayObjectSize={false} displayDataTypes={false} displayArrayKey={false}/>
        </>
    );
};

export default DockerContainerEnvTable;
