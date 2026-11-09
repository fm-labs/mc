import React from "react";
import AppIcon from "@/components/app-icon.tsx";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { toast } from "react-toastify";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";

type IconControlProps = {
    label: string
    icon: React.FC | string
    className?: string
    hidden?: boolean
    onClick?: () => Promise<void>
}

interface ContainerIconControlsProps {
    showStart?: boolean;
    showRestart?: boolean;
    showPause?: boolean;
    showStop?: boolean;
    showRemove?: boolean;
    showLogs?: boolean;
    showExec?: boolean;
    buttonProps?: React.ComponentProps<"button">;
}

const ContainerIconControls = (props: ContainerIconControlsProps) => {
    const {
        container,
        handleContainerActionClick,
    } = useDockerContainer();

    const { fetchContainers, fetchSummary } = useContainerHost()

    const containerStatus = container?.State?.Status;

    const handleActionClick = (action: string, payload?: any) => async () => {
        const p = handleContainerActionClick(action, payload);
        return toast.promise(p, {
            pending: `Executing ${action}...`,
            success: `${action.charAt(0).toUpperCase() + action.slice(1)} executed successfully!`,
            error: `Error executing ${action}`,
        }).then(() => {
            // wait a little, then refetch container data
            setTimeout(() => {
                fetchContainers(true);
                fetchSummary(true);
            }, 2000)
        })
    }

    const controls = React.useMemo(() => {
        const _controls: IconControlProps[] = [];
        if (containerStatus!=="running" && props.showStart!==false) {
            _controls.push({
                label: containerStatus === "paused" ? "Unpause" : "Start",
                icon: "start",
                onClick: handleActionClick(containerStatus === "paused" ? "unpause" : "start"),
                className: "text-green-500"
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
                className: "text-blue-300"
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
                className: "text-red-400"
            });
        }

        return _controls;
    }, [containerStatus, props.showStart, props.showPause, props.showStop, props.showRestart, props.showRemove]);

    return (
        <div className={"flex gap-1"}>
             {controls.map((control, idx) => {
                 return (
                     <span
                         key={idx}
                         title={control.label + " " + container?.Name?.substring(1)}
                         onClick={control.onClick}
                         className={control?.className}
                     >
                         <AppIcon icon={control.icon} />
                     </span>
                 );
             })}
        </div>
    );
};

export default ContainerIconControls;
