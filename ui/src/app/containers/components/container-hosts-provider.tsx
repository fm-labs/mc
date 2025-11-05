import React from "react";

type ContainerHostsContextType = {
    hosts: any[]
}

export const ContainerHostsContext = React.createContext<ContainerHostsContextType | undefined>(undefined);

export const ContainerHostsProvider: React.FC<React.PropsWithChildren<{ hosts: any[] }>> = ({
    hosts,
    children,
}) => {
    console.log("Container Hosts Provider", hosts);

    return (
        <ContainerHostsContext.Provider value={{ hosts }}>
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
