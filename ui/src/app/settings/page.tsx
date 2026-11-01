import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import ConfigFileEditor from "@/app/settings/components/config-file-editor.tsx";

const SettingsPage = () => {
    return (
        <MainContent>
            <Header title="Settings" subtitle="View and edit server configuration files." />
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
