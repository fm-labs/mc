import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ConfigFileEditor from "@/app/manage/settings/components/config-file-editor.tsx";
import { useParams } from "react-router";

const SettingsPage = () => {
    const { hostId } = useParams<{ hostId: string }>();

    return (
        <MainContent>
            <Header title={"Settings"} subtitle={`View and edit the server configuration on ${hostId}.`} />
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

export default SettingsPage;
