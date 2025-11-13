import React, {PropsWithChildren} from "react";
import {useApi} from "@/context/api-context.tsx";

type ContainerHostsContextType = {
    hosts: any[]
}

export const ContainerHostsContext = React.createContext<ContainerHostsContextType | undefined>(undefined);

export const ContainerHostsProvider = ({
                                           children,
                                       }: PropsWithChildren) => {
    const {api} = useApi();
    const [hosts, setHosts] = React.useState<any[]>([]);

    const fetchDockerHosts = async (refresh?: boolean) => {
        try {
            const response = await api.get("/api/containers/hosts?" + (refresh ? "refresh=true" : ""));
            setHosts(response);
            return response;
        } catch (error) {
            console.error("Error fetching docker hosts:", error);
            return [];
        }
    };

    React.useEffect(() => {
        fetchDockerHosts(false);
    }, []);

    console.log("Container Hosts Provider", hosts);

    return (
        <ContainerHostsContext.Provider value={{hosts}}>
            {children}
        </ContainerHostsContext.Provider>
    );
}

export const useContainerHosts = (): ContainerHostsContextType => {
    const context = React.useContext(ContainerHostsContext);
    if (!context) {
        throw new Error("useContainerHosts must be used within a ContainerHostsProvider");
    }
    return context;
}
