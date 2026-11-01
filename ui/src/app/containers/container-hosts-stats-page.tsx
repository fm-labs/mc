import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import { ContainerHostsProvider } from "@/app/containers/components/container-hosts-provider.tsx";
import ContainerHostsStats from "@/app/containers/components/stats/container-hosts-stats.tsx";

const ContainerHostsStatsPage = () => {
    return <ContainerHostsProvider>
        <ContainersLayout>
            <MainContent>
                <div>
                    <Header title={"Container Stats"}>
                        {/*<Button variant={"outline"} onClick={() => fetchDockerHosts(true)}>
                            Refresh
                        </Button>*/}
                    </Header>
                    <ContainerHostsStats />
                </div>
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default ContainerHostsStatsPage;
