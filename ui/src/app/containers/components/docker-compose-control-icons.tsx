import React from "react";
import AppIcon from "@/components/app-icon.tsx";
import { Button } from "@/components/ui/button.tsx";
import { toast } from "react-toastify";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";

type IconControlProps = {
    label: string
    icon: React.FC | string
    hidden?: boolean
    onClick?: () => Promise<void>
}

interface ComposeIconControlsProps {
    showStart?: boolean;
    showRestart?: boolean;
    showPause?: boolean;
    showStop?: boolean;
    showRemove?: boolean;
    showLogs?: boolean;
    showExec?: boolean;
    buttonProps?: React.ComponentProps<"button">;
}

const ComposeIconControls = (props: ComposeIconControlsProps) => {

    //const { fetchContainers } = useContainerHost()

    const containerStatus: string = "unknown"

    const handleComposeActionClick = async (action: string, payload?: any) => {
        console.log("compose action click", action, payload)
        throw new Error("not implemented")
    }

    const handleActionClick = (action: string, payload?: any) => async () => {
        const p = handleComposeActionClick(action, payload);
        return toast.promise(p, {
            pending: `Executing ${action}...`,
            success: `${action.charAt(0).toUpperCase() + action.slice(1)} executed successfully!`,
            error: `Error executing ${action}`,
        }).then(() => {
            //fetchContainers(true);
            return;
        })
    }

    const controls = React.useMemo(() => {
        const _controls: IconControlProps[] = [];
        if (containerStatus!=="running" && props.showStart!==false) {
            _controls.push({
                label: containerStatus === "paused" ? "Unpause" : "Start",
                icon: "start",
                onClick: handleActionClick(containerStatus === "paused" ? "unpause" : "start"),
            });
        }
        if (containerStatus==="running" && props.showPause!==false) {
            _controls.push({
                label: "Pause",
                icon: "pause",
                onClick: handleActionClick("pause"),
            });
        }
        if (containerStatus==="running" && props.showStop!==false) {
            _controls.push({
                label: "Stop",
                icon: "stop",
                onClick: handleActionClick("stop"),
            });
        }
        if (props.showRestart!==false) {
            _controls.push({
                label: "Restart",
                icon: "restart",
                onClick: handleActionClick("restart"),
            });
        }
        if (props.showRemove!==false) {
            _controls.push({
                label: "Delete",
                icon: "delete",
                onClick: handleActionClick("remove"),
            });
        }

        return _controls;
    }, [containerStatus, props.showStart, props.showPause, props.showStop, props.showRestart, props.showRemove]);

    return (
        <span className={"flex gap-1"}>
             {controls.map((control, idx) => {
                 return (
                     <span
                         key={idx}
                         title={control.label}
                         onClick={control.onClick}
                     >
                         <AppIcon icon={control.icon} />
                     </span>
                 );
             })}
        </span>
    );
};

export default ComposeIconControls;
