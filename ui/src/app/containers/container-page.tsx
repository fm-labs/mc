import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import { useParams } from "react-router";
import { ContainerHostProvider } from "@/app/containers/components/container-host-provider.tsx";
import { useApi } from "@/context/api-context.tsx";
import ContainerView from "@/app/containers/container-view.tsx";


const ContainerPage = () => {
    const { hostId, containerId } = useParams<{ hostId: string, containerId: string }>();
    const { api } = useApi();

    if (!hostId) {
        return <div>Host ID missing</div>
    }
    if (!containerId) {
        return <div>Container ID missing</div>
    }

    // const fetchDockerHosts = async (refresh?: boolean) => {
    //     try {
    //         const response = await api.get('/api/containers/hosts?' + (refresh ? 'refresh=true' : ''));
    //         setDockerHosts(response);
    //         return response;
    //     } catch (error) {
    //         console.error("Error fetching docker hosts:", error);
    //         return [];
    //     }
    // }
    //
    // React.useEffect(() => {
    //     fetchDockerHosts(false);
    // }, []);
    //
    // const hostExists = dockerHosts && dockerHosts.some(host => host.id === hostId);
    // if (!hostExists) {
    //     return <MainContent><p>Docker Host with ID {hostId} not found.</p></MainContent>;
    // }

    return (
        <MainContent>
            <ContainerHostProvider config={{hostId}}>
                <ContainerView containerId={containerId} />
            </ContainerHostProvider>
        </MainContent>
    );
};

export default ContainerPage;
