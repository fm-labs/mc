import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import React from "react";
import { KeyValueTable } from "@/components/key-value-table.tsx";

const DockerContainerEnvTable = () => {
    const { container } = useDockerContainer()
    const kvData = React.useMemo(() => {
        return Object.entries(container)
            .filter((entry) => entry[0].endsWith('Path') && entry[0] !== 'Path')
            .map((entry) => {
                return {
                    key: entry[0],
                    value: entry[1],
                }
            })
    }, [container])

    return (
        <>
            <KeyValueTable data={kvData} />
        </>
    );
};

export default DockerContainerEnvTable;
