import { Icon3dCubeSphere, IconCube, IconCubeOff } from "@tabler/icons-react";

export const DockerContainerStatus = ({ status, showText }: { status: string, showText?: boolean }) => {
    //let colorClass = "bg-gray-500";
    let color = "gray";
    if (status==="running") {
        //colorClass = "bg-green-500";
        color = "green";
    } else if (status==="exited") {
        //colorClass = "bg-red-500";
        color = "red";
    } else if (status==="paused") {
        //colorClass = "bg-yellow-500";
        color = "yellow";
    }

    return (
        <span>
            {/*<Icon3dCubeSphere />*/}
            {/*<IconCubeOff />*/}
            <span className={`inline-block ml-1 w-4 h-3`} title={status}>
                <IconCube size={"1em"} color={color} />
            </span>
            {showText && ` ${status}`}
        </span>
    );
};
