import React from "react";
import Data from "@/components/data.tsx";
import { EventSourceReader } from "@/components/event-source-reader.tsx";
import { DockerContainerStatus } from "@/app/containers/components/docker-container-status.tsx";
import DockerContainerState from "@/app/containers/components/docker-container-state.tsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import DockerContainerLabelsTable from "@/app/containers/components/docker-container-labels-table.tsx";
import { DockerContainerMountsTable } from "@/app/containers/components/docker-container-mounts-table.tsx";
import { DockerContainerProvider, useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import DockerContainerControlIcons from "@/app/containers/components/docker-container-control-icons.tsx";
import DockerContainerPorts from "@/app/containers/components/docker-container-ports.tsx";
import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import DockerContainerEnvTable from "@/app/containers/components/docker-container-env-table.tsx";
import DockerContainerNetworksTable from "@/app/containers/components/docker-container-networks-table.tsx";
import DockerContainerPathsTable from "@/app/containers/components/docker-container-paths-table.tsx";
import DockerContainerExec from "@/app/containers/components/docker-container-exec.tsx";
import { useApi } from "@/context/api-context.tsx";
import { Layers } from "lucide-react";
import DockerContainerInspect from "@/app/containers/components/docker-container-inspect.tsx";
import DockerContainerUptime from "@/app/containers/components/docker-container-uptime.tsx";

// const logMessageFormatter = (message: string) => {
//     try {
//         const logEntry = JSON.parse(message);
//         const { log } = logEntry;
//         //return `${line} | ${log}`;
//         return log;
//     } catch (e) {
//         return message;
//     }
// };

export const DockerContainersListItem = ({ open }: { open?: true}) => {
    const { container, buildLogStreamUrl } = useDockerContainer()
    const [selectedContainerId, setSelectedContainerId] = React.useState<string | null>(open ? container.Id : null);
    const containerLogStreamUrl = buildLogStreamUrl(container?.Id);

    return <div>
        <div className={"flex flex-start space-x-2"}>
            <div className={"flex space-x-1"}>
                <DockerContainerStatus status={container.State?.Status} />
                <span className={selectedContainerId===container.Id ? "font-bold":""}
                      onClick={() => {
                          if (selectedContainerId===container.Id) {
                              setSelectedContainerId(null);
                              return;
                          }
                          setSelectedContainerId(container.Id);
                      }}>{container?.Name?.substring(1) || "Unknown name"}
                                            </span>
            </div>
            <div className={"flex items-center space-x-1"}>
                <div className={"text-muted-foreground text-xs ml-1"}>
                    {container?.Config?.Image || container?.Image}
                </div>
                <DockerContainerState state={container.State} />
                <DockerContainerUptime />
                <Data data={container} />
            </div>
        </div>
        {selectedContainerId===container.Id
            && <>
                <div className={"text-muted-foreground text-xs ml-6"}><DockerContainerPorts
                    ports={container?.NetworkSettings?.Ports} /></div>

                <Tabs defaultValue="logs" className={"mt-2"}>
                    <div className={"flex justify-between items-center"}>
                        <TabsList>
                            <TabsTrigger value="logs">Logs</TabsTrigger>
                            <TabsTrigger value="inspect">Inspect</TabsTrigger>
                            <TabsTrigger value="labels">Labels</TabsTrigger>
                            <TabsTrigger value="mounts">Mounts</TabsTrigger>
                            <TabsTrigger value="environment">Environment</TabsTrigger>
                            <TabsTrigger value="networks">Networks</TabsTrigger>
                            <TabsTrigger value="paths">Paths</TabsTrigger>
                            <TabsTrigger value="exec">Exec</TabsTrigger>
                        </TabsList>
                        <DockerContainerControlIcons />
                    </div>
                    <div className={"border border-t-0 rounded-b p-2 max-h-[400px] overflow-auto bg-background shadow"}>
                        <TabsContent value="labels">
                            <DockerContainerLabelsTable />
                        </TabsContent>
                        <TabsContent value="inspect">
                            <DockerContainerInspect />
                        </TabsContent>
                        <TabsContent value="mounts">
                            <DockerContainerMountsTable />
                        </TabsContent>
                        <TabsContent value="environment">
                            <DockerContainerEnvTable />
                        </TabsContent>
                        <TabsContent value="paths">
                            <DockerContainerPathsTable />
                        </TabsContent>
                        <TabsContent value="networks">
                            <DockerContainerNetworksTable />
                        </TabsContent>
                        <TabsContent value="exec">
                            <DockerContainerExec />
                        </TabsContent>
                        <TabsContent value="logs">
                            {containerLogStreamUrl}
                            {containerLogStreamUrl
                                && (<EventSourceReader url={containerLogStreamUrl}
                                    /*logFormatter={logMessageFormatter}*/ />)}
                        </TabsContent>
                    </div>
                </Tabs>
            </>}
    </div>
}


const DockerContainersList = () => {
    const { config, containers, fetchContainers } = useContainerHost();
    const {apiBaseUrl} = useApi()
    const [selectedContainer, setSelectedContainer] = React.useState<string | null>(null);

    //const [autorefreshInterval, setAutoRefreshInterval] = React.useState<number | null>(30000);

    const containerLogStreamUrl = React.useMemo(() => selectedContainer
            ? `${apiBaseUrl}api/containers/${config.hostId}/containers/${selectedContainer}/logs/stream`:null,
        [selectedContainer, config.hostId, apiBaseUrl]);

    const groupedData = React.useMemo(() => {
        if (!containers) return {};

        const grouped = containers.reduce((acc: any, row: any) => {
            const key = row?.Config?.Labels?.["com.docker.compose.project"] ?? "_";
            (acc[key] ??= []).push(row);
            return acc;
        }, {} as Record<string, any[]>);

        return Object.fromEntries(
            Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)),
        );
    }, [containers]);

    // React.useEffect(() => {
    //     // Auto-refresh
    //     let intervalId: any;
    //     if (autorefreshInterval && autorefreshInterval > 0) {
    //         // modifying the interval withing a range to avoid too much parallel requests
    //         // if many hosts are monitored at the same time
    //         const min_interval = Math.max(5000, autorefreshInterval - 2000);
    //         const max_interval = autorefreshInterval + 2000;
    //         const _interval = Math.floor(Math.random() * (max_interval - min_interval + 1)) + min_interval;
    //         console.log("Docker AutorefreshInterval (without/with jitter):", autorefreshInterval, _interval);
    //         intervalId = setInterval(fetchContainers, _interval);
    //     }
    //
    //     return () => {
    //         if (intervalId) {
    //             clearInterval(intervalId);
    //         }
    //     };
    // }, []);

    if (!containers) {
        return <p>No containers found.</p>;
    }

    return (
        <div>
            {Object.entries(groupedData).map(([group, _containers]: [string, any]) => {
                return (<div key={group} className={"mb-2"}>
                    <h3 className={"text-muted-foreground font-bold border-l-4 pl-1"}>
                        <Layers className={"inline-block w-4 h-4 ml-1 mr-2"} />
                        {group}
                    </h3>
                    <ul>
                        {_containers.map((container: any) => (
                            <li key={container.Id}
                                className={`cursor-pointer pb-1 pl-1 pt-1 border-l-4 hover:border-l-amber-400 ${selectedContainer===container.Id ? "bg-accent pb-2":""}`}>
                                <DockerContainerProvider container={container}>
                                    <DockerContainersListItem />
                                </DockerContainerProvider>
                            </li>
                        ))}
                    </ul>
                </div>);
            })}
        </div>
    );
};

export default DockerContainersList;
