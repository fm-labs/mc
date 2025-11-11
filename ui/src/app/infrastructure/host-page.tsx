import React from "react";
import { useLoaderData } from "react-router";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import { Button } from "@/components/ui/button.tsx";
import ReactJson from "@microlink/react-json-view";
import NetworkArchMermaid from "@/app/infrastructure/network/network-arch-mermaid.tsx";
import { EventSourceReader } from "@/components/event-source-reader.tsx";
import HostServices from "@/app/infrastructure/host/host-services.tsx";
import { HostProvider } from "@/app/infrastructure/host/host-provider.tsx";
import HostFindings from "@/app/infrastructure/host/host-findings.tsx";
import { FindingsProvider } from "@/app/findings/components/findings-provider.tsx";
import { useApi } from "@/context/api-context.tsx";

const HostPage = () => {
    const { apiBaseUrl } = useApi();
    const host: InventoryItem<any> = useLoaderData();
    const [streamUrl, setStreamUrl] = React.useState<string | null>(null);

    const handleStreamLogs = (logType: string) => {
        const url = `${apiBaseUrl}/api/infrastructure/host/${host.item_key}/logs/stream?type=${logType}`;
        if (streamUrl===url) {
            // If the same log type is clicked again, stop streaming
            setStreamUrl(null);
        } else {
            setStreamUrl(url);
        }
    };

    React.useEffect(() => {
        console.log("HostPage host:", host);
    }, [host]);

    return (
        <HostProvider host={host}>
            <MainContent>
                <Header
                    title={`Host ${host.name}`}
                    subtitle={`IP: ${host?.properties?.ipAddress || "No IP"} - OS: ${host?.properties?.os || "Unknown OS"} - Network: ${host?.properties?.network || "No Network"}`}>
                    <div>
                        <Button>
                            Edit Host
                        </Button>{" "}
                        <Button>
                            Launch App
                        </Button>
                    </div>
                </Header>

                {/* HOST TABS */}
                <div className="mt-4">
                    <Tabs defaultValue="findings" className={"mt-2"}>
                        <div className={"flex justify-between items-center"}>
                            <TabsList>
                                <TabsTrigger value="services">Services & Apps</TabsTrigger>
                                <TabsTrigger value="findings">Findings</TabsTrigger>
                                <TabsTrigger value="info">Host Info</TabsTrigger>
                                <TabsTrigger value="logs">Logs</TabsTrigger>
                            </TabsList>
                        </div>
                        <TabsContent value="info">
                            <div className={"flex flex-row w-full"}>
                                <div
                                    className={"w-1/2 border border-gray-200 p-2 rounded mr-2 overflow-auto max-h-[600px]"}>
                                    <ReactJson src={host} collapsed={false} name={false} enableClipboard={true}
                                               displayDataTypes={false} />
                                </div>
                                <div className={"w-1/2"}>
                                    <NetworkArchMermaid />
                                </div>
                            </div>
                        </TabsContent>
                        <TabsContent value="findings">
                            <FindingsProvider initialFilters={{ resource_type: "host", resource_name: host.name }}>
                                <HostFindings />
                            </FindingsProvider>
                        </TabsContent>
                        <TabsContent value="services">
                            <HostServices />
                        </TabsContent>
                        <TabsContent value="logs">
                            <div>
                                <div>
                                    <Button onClick={() => handleStreamLogs("syslog")}>
                                        Stream Syslog
                                    </Button>
                                    <Button onClick={() => handleStreamLogs("systemd")}>
                                        Stream Systemd Logs
                                    </Button>
                                    <Button onClick={() => handleStreamLogs("kernel")}>
                                        Stream Kernel Logs
                                    </Button>
                                    <Button onClick={() => handleStreamLogs("auth")}>
                                        Stream Auth Logs
                                    </Button>
                                </div>

                                <hr />
                                {streamUrl && <EventSourceReader url={streamUrl} />}
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </MainContent>
        </HostProvider>
    );
};

export default HostPage;
