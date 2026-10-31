import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import React from "react";

export const DockerHostStatus = ({showText}: { showText?: boolean }) => {
    const {summary, enabled} = useContainerHost();
    const status = enabled ? (summary ? "Connected" : "Disconnected") : "Disabled";

    const colorClass = React.useMemo(() => {
        let colorClass = "bg-gray-500";
        if (status.toLowerCase() === "connected") {
            colorClass = "bg-green-500";
        } else if (status.toLowerCase() === "disconnected") {
            colorClass = "bg-red-500";
        }
        return colorClass
    }, [status])

    return (
        <span>
            <span className={`inline-block ml-1 w-3 h-3 rounded-full ${colorClass}`} title={status}></span>
            {showText && ` ${status}`}
        </span>
    );
};
