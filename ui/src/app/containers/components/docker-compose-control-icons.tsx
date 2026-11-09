import React from "react";
import AppIcon from "@/components/app-icon.tsx";
import { toast } from "react-toastify";
import { useApi } from "@/context/api-context.tsx";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";

type IconControlProps = {
    label: string
    icon: React.FC | string
    className?: string
    onClick?: () => Promise<void>
}

// actions of POST /api/containers/{host}/compose/{project}/actions/{action}
type ComposeAction = "up" | "stop" | "restart" | "down";

const ACTION_LABELS: Record<ComposeAction, string> = {
    up: "Start",
    stop: "Stop",
    restart: "Restart",
    down: "Delete",
};

interface ComposeIconControlsProps {
    projectName: string;
    // the project's containers (docker inspect attrs), for the project state
    containers: any[];
    // called after an action finished, e.g. to reload the containers
    onActionDone?: () => void;
    showStart?: boolean;
    showRestart?: boolean;
    showStop?: boolean;
    showRemove?: boolean;
}

const ComposeIconControls = (props: ComposeIconControlsProps) => {
    const { projectName, containers, onActionDone } = props;
    const { api } = useApi();
    const { config, fetchSummary } = useContainerHost();

    const statuses: string[] = containers.map((c) => c?.State?.Status);
    const allRunning = statuses.length > 0 && statuses.every((s) => s === "running");
    const anyRunning = statuses.some((s) => s === "running" || s === "paused" || s === "restarting");

    const handleActionClick = (action: ComposeAction) => async () => {
        const label = ACTION_LABELS[action];
        if (action === "down"
            && !window.confirm(`Delete all ${containers.length} containers of compose project "${projectName}"?`)) {
            return;
        }
        const p = api.post(`/api/containers/${config.hostId}/compose/${encodeURIComponent(projectName)}/actions/${action}`);
        return toast.promise(p, {
            pending: `${label} ${projectName}...`,
            success: `${label} ${projectName} executed successfully!`,
            error: {
                render: ({ data }: any) => data?.response?.data?.detail || `Error executing ${label} on ${projectName}`,
            },
        }).then(() => {
            // wait a little, then refetch container data
            setTimeout(() => {
                onActionDone?.();
                fetchSummary(true);
            }, 2000);
        }).catch(() => {
            // a part of the containers may have changed
            onActionDone?.();
        });
    };

    const controls: IconControlProps[] = [];
    if (!allRunning && props.showStart !== false) {
        controls.push({ label: ACTION_LABELS.up, icon: "start", onClick: handleActionClick("up"), className: "text-green-500" });
    }
    if (anyRunning && props.showStop !== false) {
        controls.push({ label: ACTION_LABELS.stop, icon: "stop", onClick: handleActionClick("stop"), className: "text-blue-300" });
    }
    if (props.showRestart !== false) {
        controls.push({ label: ACTION_LABELS.restart, icon: "restart", onClick: handleActionClick("restart") });
    }
    if (props.showRemove !== false) {
        controls.push({ label: ACTION_LABELS.down, icon: "delete", onClick: handleActionClick("down"), className: "text-red-400" });
    }

    return (
        <span className={"flex gap-1"}>
            {controls.map((control) => (
                <span key={control.label}
                      title={`${control.label} ${projectName}`}
                      onClick={control.onClick}
                      className={"cursor-pointer " + (control.className ?? "")}>
                    <AppIcon icon={control.icon} />
                </span>
            ))}
        </span>
    );
};

export default ComposeIconControls;
