import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import { ContainerHostsProvider } from "@/app/containers/components/container-hosts-provider.tsx";
import DockerHostsKitchensink from "@/app/containers/components/docker-host-kitchensink.tsx";

const ContainerHostsPage = () => {
    return <ContainerHostsProvider>
        <ContainersLayout>
            <MainContent>
                <div>
                    <Header title={"Containers"}>
                        {/*<Button variant={"outline"} onClick={() => fetchDockerHosts(true)}>
                            Refresh
                        </Button>*/}
                    </Header>
                    {/*<DockerHostsGrid />*/}
                    <DockerHostsKitchensink />
                </div>
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default ContainerHostsPage;
