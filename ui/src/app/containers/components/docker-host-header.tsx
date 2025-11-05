import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import { Link } from "react-router";
import { Button } from "@/components/ui/button.tsx";
import Header from "@/components/header.tsx";

const DockerHostHeader = () => {
    const { config, info } = useContainerHost()

    return (
        <div>
            <Button asChild variant="link" className="p-0 mb-1">
                <Link to={'..'}>{'< '}List docker hosts</Link>
            </Button>
            <Header title={`Docker Host ID: ${config.hostId}`} subtitle={`Docker Host ID: ${config.hostId}`}>
                {info && info.Name &&
                    <div className={"text-sm text-muted-foreground"}>
                        Name: {info.Name} |
                        OS: {info.OperatingSystem} |
                        Docker Version: {info.ServerVersion} |
                        Containers: {info.Containers} (Running: {info.ContainersRunning}, Paused: {info.ContainersPaused}, Stopped: {info.ContainersStopped}) | Images: {info.Images}
                    </div>}
            </Header>
        </div>
    );
};

export default DockerHostHeader;
