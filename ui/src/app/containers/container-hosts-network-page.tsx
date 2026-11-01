import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import {ContainerHostsProvider} from "@/app/containers/components/container-hosts-provider.tsx";
import ContainerHostsNetwork from "@/app/containers/components/network/container-hosts-network.tsx";

const ContainerHostsNetworkPage = () => {
    return <ContainerHostsProvider>
        <ContainersLayout>
            <MainContent>
                <div>
                    <Header title={"Container Network"}
                            subtitle={"How networks and containers connect on each connected host"}/>
                    <ContainerHostsNetwork/>
                </div>
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default ContainerHostsNetworkPage;
