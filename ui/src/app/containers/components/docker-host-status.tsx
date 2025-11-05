import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import { Icon3dCubeSphere, IconCube, IconCubeOff } from "@tabler/icons-react";

export const DockerHostStatus = ({ showText }: { showText?: boolean }) => {
    const { summary } = useContainerHost();
    const status = summary ? "Connected" : "Disconnected";

    let colorClass = "bg-gray-500";
    if (status.toLowerCase() === "connected") {
        colorClass = "bg-green-500";
    } else if (status.toLowerCase() === "disconnected") {
        colorClass = "bg-red-500";
    }

    return (
        <span>
            <span className={`inline-block ml-1 w-3 h-3 rounded-full ${colorClass}`} title={status}></span>
            {showText && ` ${status}`}
        </span>
    );
};
