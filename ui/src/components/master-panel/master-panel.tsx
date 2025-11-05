import AppIcon from "@/components/app-icon.tsx";
import { MasterContextProvider } from "@/components/master-panel/master-context-provider.tsx";
import React, { PropsWithChildren, ReactNode } from "react";
import MasterPanelOutputWriterTab from "@/components/master-panel/master-panel-output-writer-tab.tsx";
import MasterPanelInputTab from "@/components/master-panel/master-panel-input-tab.tsx";
import useDialog from "@/hooks/use-dialog.tsx";

const MasterPanelTab = (props: PropsWithChildren<any>) => {
    return (
        <div className={"tabs cursor-pointer " + props?.className}>{props.children}</div>
    );
};

/**
 * MasterPanel component
 * A container component for the master panel section of the application.
 *
 * The master panel sticks to the bottom of the viewport in minimized mode
 * and expands to show additional content when activated.
 *
 * The panel contains multiple tabs for different functionalities.
 *
 * @constructor
 */
const MasterPanel = () => {
    const { createDrawer } = useDialog();
    const [currentDialog, setCurrentDialog] = React.useState<ReactNode>();

    const handleTabClick = (element: ReactNode) => {
        const dialog = createDrawer({
            title: "Tab Content",
            children: element, onClose: () => setCurrentDialog(undefined),
            size: "lg",
        });
        setCurrentDialog(dialog);
    };

    return (
        <MasterContextProvider>
            <div id={"master-panel"}
                 style={{ zIndex: 9999 }}
                 className={"master-panel fixed bottom-0 left-0 w-full h-8 bg-lime-900 text-white text-xs transition-all duration-300 ease-in-out opacity-50 hover:opacity-100"}>
                <div
                    className={"tabs flex gap-x-2 justify-between items-center h-full px-2 overflow-x-auto no-scrollbar"}>

                    <div className={"flex gap-x-2 justify-start items-center"}>
                        <MasterPanelTab>
                                <span
                                    onClick={() => handleTabClick(<div>HUHUU</div>)}>
                                    <AppIcon icon={"docker"} />
                                </span>
                        </MasterPanelTab>
                        <MasterPanelTab><AppIcon icon={"globe"} /></MasterPanelTab>
                        <MasterPanelTab><AppIcon icon={"container"} /></MasterPanelTab>
                        <MasterPanelTab><AppIcon icon={"console"} /></MasterPanelTab>
                        <MasterPanelInputTab />
                    </div>
                    <div className={"flex gap-x-2 justify-start items-center"}>
                        <MasterPanelOutputWriterTab />
                        <MasterPanelTab><AppIcon icon={"tool"} /></MasterPanelTab>
                    </div>
                </div>

            </div>
            {currentDialog}
        </MasterContextProvider>
    );
};

MasterPanel.Tab = MasterPanelTab;

export default MasterPanel;
