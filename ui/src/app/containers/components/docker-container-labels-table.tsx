import React from "react";
import { KeyValueTable } from "@/components/key-value-table.tsx";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";

const DockerContainerLabelsTable = () => {
    const { container } = useDockerContainer();
    const labels = container?.Config?.Labels

    const kvData = React.useMemo(() => {
        if (!labels) return [];
        return Object.entries(labels).map((entry) => {
            return {
                key: entry[0],
                value: entry[1],
            };
        });
    }, [labels]);

    return (
        <>
            <KeyValueTable data={kvData} />
        </>
    );
};

export default DockerContainerLabelsTable;
