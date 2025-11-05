import { IconNetwork } from "@tabler/icons-react";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { NetworkProvider } from "@/app/infrastructure/network/network-provider.tsx";
import NetworkHosts from "@/app/infrastructure/network/network-hosts.tsx";
import NetworkArchMermaid from "@/app/infrastructure/network/network-arch-mermaid.tsx";
import React from "react";
import { Badge } from "@/components/ui/badge.tsx";
import { Share2Icon } from "lucide-react";

const NetworksGrid = ({ networks }: { networks: InventoryItem<any>[] }) => {
    const [selectedNetwork, setSelectedNetwork] = React.useState<InventoryItem<any> | null>(null);

    const toggleSelectedNetwork = (network: InventoryItem<any>) => {
        if (selectedNetwork && selectedNetwork.name===network.name) {
            setSelectedNetwork(null);
        } else {
            setSelectedNetwork(network);
        }
    };

    return (
        <div>
            <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {networks && networks.length > 0 && networks.map((network) => (
                    <li
                        key={network.name}
                        className="rounded-lg border p-4 hover:shadow-md"
                    >
                        <NetworkProvider network={network}>
                            <div className="mb-4 flex items-center justify-between">
                                <div
                                    className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
                                    onClick={() => toggleSelectedNetwork(network)}
                                >
                                    <Share2Icon />
                                </div>
                                <div>
                                    {/*<Button
                                        variant="outline"
                                        size="sm"
                                        //onClick={() => setCurrentNetwork(network, null)}
                                        //className={`${network.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                                    >
                                        Add Host
                                    </Button>*/}{" "}
                                    {/*<Button
                                        variant="outline"
                                        size="sm"
                                        //onClick={() => setCurrentNetwork(network, null)}
                                        //className={`${network.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                                    >
                                        Launch new Host
                                    </Button>*/}
                                </div>
                            </div>
                            <div>
                                <h2 className="mb-1 font-semibold">{network.name}</h2>
                                <div className="flex gap-1 line-clamp-2 text-gray-500 text-sm">
                                    {network?.properties?.cidr}
                                    <Badge variant={"outline"}>{network?.properties?.category}</Badge>
                                    <Badge variant={"secondary"}>{network?.properties?.visibility}</Badge>
                                </div>
                                <NetworkHosts />
                                {selectedNetwork && selectedNetwork.name===network.name && <NetworkArchMermaid />}
                            </div>
                        </NetworkProvider>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default NetworksGrid;
