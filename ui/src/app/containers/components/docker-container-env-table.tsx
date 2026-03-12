import {useDockerContainer} from "@/app/containers/components/docker-container-provider.tsx";
import React from "react";
import {KeyValueTable} from "@/components/key-value-table.tsx";

const DockerContainerEnvTable = () => {
    const {container} = useDockerContainer()
    const env = container?.Config?.Env;

    const kvData = React.useMemo(() => {
        if (!env) return [];
        return Object.entries(env)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map((entry) => {
                return {
                    key: entry[0],
                    value: entry[1],
                };
            });
    }, [env]);

    return (
        <>
            <KeyValueTable data={kvData}/>
        </>
    );
};

export default DockerContainerEnvTable;
