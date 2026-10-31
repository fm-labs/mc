import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";

const DockerHostEngine = () => {
    const {summary, info} = useContainerHost()

    return (
        <div>
            <h1>Host Engine Info</h1>

            <h2>Info</h2>
            <pre>{JSON.stringify(info, null, 2)}</pre>
            <hr />

            <h2>Summary</h2>
            <pre>{JSON.stringify(summary, null, 2)}</pre>
        </div>
    );
};

export default DockerHostEngine;