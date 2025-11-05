import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import Header from "@/components/header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import { ContainerHostsProvider } from "@/app/containers/components/container-hosts-provider.tsx";
import DockerHostsKitchensink from "@/app/containers/components/docker-host-kitchensink.tsx";


const ContainerHostsPage = () => {
    const { api } = useApi();
    const [dockerHosts, setDockerHosts] = React.useState<any[]>([]);

    const fetchDockerHosts = async (refresh?: boolean) => {
        try {
            const response = await api.get("/api/containers/hosts?" + (refresh ? "refresh=true":""));
            setDockerHosts(response);
            return response;
        } catch (error) {
            console.error("Error fetching docker hosts:", error);
            return [];
        }
    };

    React.useEffect(() => {
        fetchDockerHosts(false);
    }, []);

    return <ContainerHostsProvider hosts={dockerHosts}>
        <ContainersLayout>
            <MainContent>
                <div>
                    <Header title={"Containers"}>
                        <Button variant={"outline"} onClick={() => fetchDockerHosts(true)}>
                            Refresh
                        </Button>
                    </Header>
                    {/*<DockerHostsGrid hosts={dockerHosts} />*/}
                    <DockerHostsKitchensink hosts={dockerHosts} />
                </div>
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default ContainerHostsPage;
