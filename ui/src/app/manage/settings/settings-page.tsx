import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ConfigFileEditor from "@/app/manage/settings/components/config-file-editor.tsx";
import {useParams} from "react-router";
import {ContainerHostsProvider} from "@/app/containers/components/container-hosts-provider.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import React from "react";

const SettingsView = ({hostId}: {hostId?: string}) => {
    return (
        <MainContent>
            <ConfigFileEditor
                conf="mc"
                title="Mission Control"
                description="Main configuration (mc.conf.json). Most changes take effect after a restart."
            />
            <ConfigFileEditor
                conf="ssh"
                title="SSH"
                description="SSH client config used for connections to remote hosts."
            />
        </MainContent>
    );
};

const SettingsPage = () => {
    const {hostId} = useParams<{ hostId: string }>();
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return <ContainerHostsProvider>
        <ContainersLayout>
            <MainContent>
                <Header title={"Settings"} subtitle={`View and edit server configuration on *${hostId}*`} />
                <SettingsView hostId={hostId} />
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};


export default SettingsPage;
