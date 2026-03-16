import React, { PropsWithChildren } from "react";
import { TaskStatusResponse } from "@/features/tasks/tasks.types.ts";
import { useApi } from "@/context/api-context.tsx";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";


type DockerContainerContextType = {
    hostId: string;
    container: any,
    handleContainerActionClick: (action: string, payload?: any) => () => Promise<void | TaskStatusResponse>
    buildLogStreamUrl: (containerId: string) => string
}

const DockerContainerContext = React.createContext<DockerContainerContextType | undefined>(undefined);

export const useDockerContainer = (): DockerContainerContextType => {
    const context = React.useContext(DockerContainerContext);
    if (!context) {
        throw new Error("useDockerContainer must be used within a DockerContainerProvider");
    }
    return context;
};

export const DockerContainerProvider = ({
                                            children,
                                            container,
                                        }: PropsWithChildren<{ container: any }>) => {
    const { api, apiBaseUrl } = useApi();
    const { config } = useContainerHost();

    const handleContainerActionClick = (containerId: string) => (_action: string, _payload?: any) => {
        console.log("Container action", containerId, _action, _payload);
        return api.post(`/api/containers/${config.hostId}/containers/${containerId}/actions/${_action}`, _payload)
    };

    const buildLogStreamUrl = (containerId: string) => {
        //return `${apiBaseUrl}/api/containers/${config.hostId}/containers/${containerId}/logs/stream?t=${localStorage.getItem("authToken") || ""}`;
        return `${apiBaseUrl}/api/containers/${config.hostId}/containers/${containerId}/logs/stream`;
    }

    return (<DockerContainerContext.Provider value={{
            hostId: config.hostId,
            container,
            handleContainerActionClick: handleContainerActionClick(container.Id),
            buildLogStreamUrl,
        }}>
            {children}
        </DockerContainerContext.Provider>
    );


};

