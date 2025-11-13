import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import Header from "@/components/header.tsx";

const DockerHostHeader = ({ subtitle } : { subtitle?: string}) => {
    const { config, info } = useContainerHost()

    return (
        <div>
            {/*<Button asChild variant="link" className="p-0 mb-1">*/}
            {/*    <Link to={'..'}>{'< '}All docker hosts</Link>*/}
            {/*</Button>*/}
            <Header title={`${config.hostId}`} subtitle={subtitle || 'Container Host'}>
                <div>
                {info && info.Name &&
                    <div className={"text-sm text-muted-foreground"}>
                        Name: {info.Name} |
                        OS: {info.OperatingSystem} |
                        Docker Version: {info.ServerVersion} |
                        Containers: {info.Containers} (Running: {info.ContainersRunning}, Paused: {info.ContainersPaused}, Stopped: {info.ContainersStopped}) | Images: {info.Images}
                    </div>}
                </div>
            </Header>
        </div>
    );
};

export default DockerHostHeader;
