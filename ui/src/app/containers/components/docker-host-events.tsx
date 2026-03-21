import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import {EventStreamReader} from "@/components/event-stream-reader.tsx";

const DockerHostEvents = () => {
    const {getHostApiEndpointUrl} = useContainerHost()

    const eventStreamUrl = React.useMemo(() => {
        return getHostApiEndpointUrl("events/stream")
    }, [getHostApiEndpointUrl]);

    return (
        <div>
            <DockerHostHeader title={"Events"}/>
            {eventStreamUrl && (<EventStreamReader url={eventStreamUrl}
                                                   headers={{"Authorization": "Bearer " + localStorage.getItem("authToken")!}}
                                                   logFormatter={undefined}/>)}
        </div>
    );
};

export default DockerHostEvents;