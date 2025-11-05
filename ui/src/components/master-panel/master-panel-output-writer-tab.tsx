import TypewriterText from "@/components/typewriter-text.tsx";
import { useMasterContext } from "@/components/master-panel/master-context-provider.tsx";
import MasterPanel from "./master-panel";

const MasterPanelOutputWriterTab = () => {
    const { lastNotification } = useMasterContext()

    return (
        <MasterPanel.Tab className={"tab cursor-pointer flex-1"}>
            <TypewriterText delay={2000} speed={50} repeat={false} text={lastNotification || ""}>
                {lastNotification}
            </TypewriterText>
        </MasterPanel.Tab>
    );
};

export default MasterPanelOutputWriterTab;
