import MainContent from "@/components/layout/main-content.tsx";
import { AwsInventoryProvider, useAwsInventory } from "@/app/aws/aws-inventory-provider.tsx";
import Data from "@/components/data.tsx";
import GraphVisualization from "@/app/aws/components/graph-visualization.tsx";
import React from "react";

const AwsEc2InstancState = ({ status }: { status: string }) => {
    let colorClass = "text-gray-500";
    if (status==="running") {
        colorClass = "text-green-500";
    } else if (status==="stopped") {
        colorClass = "text-red-500";
    } else if (status==="pending" || status==="stopping" || status==="shutting-down") {
        colorClass = "text-yellow-500";
    } else if (status==="terminated") {
        colorClass = "text-black";
    }

    return <span className={colorClass}>{status}</span>;
};

const AwsTags = ({ tags }: { tags: { Key: string, Value: string }[] }) => {
    if (!tags || tags.length===0) {
        //return <span className="text-muted-foreground">No Tags</span>;
        return null;
    }
    return <div className="flex flex-wrap mt-1">
        {tags.filter((t) => !t.Key.startsWith("aws:"))
            .map((tag) => (
                <span key={tag.Key} className="text-muted-foreground mr-2">
                {tag.Key}: {tag.Value}
            </span>
            ))}
    </div>;
};

const AwsEc2Instances = () => {
    const { items } = useAwsInventory();

    return <div>
        <h2 className="text-sm font-bold mb-2 underline">EC2 Instances ({items?.length})</h2>
        {items && items.length > 0 ? (
            <ul className="">
                {items.map((item, idx) => (
                    <li key={idx} className="border p-1 mb-1 text-xs">
                        <div className="mb-2">
                            <strong>{item.name || item.id}</strong> {item.accountId} / {item.properties?.InstanceType}
                            <Data data={item} />
                            <div>
                                {item.properties?.PrivateIpAddress}
                                | {item.properties?.PublicIpAddress || "No Public IP"}
                                | <AwsEc2InstancState status={item.properties?.State?.Name} />
                            </div>
                            <div>
                                <AwsTags tags={item.properties?.Tags} />
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        ):(
            <p className={"text-muted-foreground"}>No EC2 Instance resources found.</p>
        )}
    </div>;
};


const AwsSubnets = () => {
    const { items } = useAwsInventory();

    return <div>
        <h2 className="text-sm font-bold mb-2 underline">Subnets ({items?.length})</h2>
        {items && items.length > 0 ? (
            <ul className="grid grid-cols-4 gap-1">
                {items.sort((a, b) => {
                    return a.properties?.CidrBlock.localeCompare(b.properties?.CidrBlock);
                }).map((item, idx) => (
                    <li key={idx} className="border p-1 mb-1 text-xs">
                        <div className="mb-4">
                            <strong>{item.name || item.id}</strong> {item.accountId} / {item.properties?.AvailabilityZone}
                            <Data data={item} />
                            <div>{item.properties?.CidrBlock} | {item.properties?.MapPublicIpOnLaunch ? "Public":"Private"}</div>
                        </div>


                        <AwsInventoryProvider filter={{
                            serviceIds: ["ec2"],
                            resourceTypes: ["AWS::EC2::Instance"],
                            properties: { SubnetId: item.properties.SubnetId },
                        }}
                        >
                            <AwsEc2Instances />
                        </AwsInventoryProvider>
                    </li>
                ))}
            </ul>
        ):(
            <p className={"text-muted-foreground"}>No Subnet resources found.</p>
        )}
    </div>;
};

const AwsNetworks = () => {
    const { items } = useAwsInventory();

    return <div>
        <h2 className="text-xl font-bold mb-2">VPC Networks ({items?.length})</h2>
        {items && items.length > 0 ? (
            <ul className="flex flex-col">
                {items.sort((a, b) => {
                    return a.properties?.CidrBlock.localeCompare(b.properties?.CidrBlock);
                }).map((item, idx) => (
                    <li key={idx} className="border p-2 mb-2 text-xs">
                        <div className="mb-4">
                            <strong>{item.name || item.id}</strong> {item.accountId} / {item.regionId}
                            <Data data={item} />
                            <div>{item.properties?.CidrBlock}</div>
                        </div>

                        <AwsInventoryProvider filter={{
                            serviceIds: ["ec2"],
                            resourceTypes: ["AWS::EC2::Subnet"],
                            properties: { VpcId: item.properties.VpcId },
                        }}
                        >
                            <AwsSubnets />
                        </AwsInventoryProvider>
                    </li>
                ))}
            </ul>
        ):(
            <p className={"text-muted-foreground"}>No VPC resources found.</p>
        )}
    </div>;
};


const AwsNetworksPage = () => {

    const [awsgraph, setAwsGraph] = React.useState(null);

    React.useEffect(() => {
        fetch('/awsgraph.json')
            .then(response => response.json())
            .then(data => setAwsGraph(data))
            .catch(error => console.error('Error fetching AWS graph data:', error));
    }, []);

    return <MainContent>
        <AwsInventoryProvider filter={{ serviceIds: ["ec2"], resourceTypes: ["AWS::EC2::Vpc"] }}>
            <AwsNetworks />
        </AwsInventoryProvider>
        {awsgraph && <GraphVisualization data={awsgraph as any} />}
    </MainContent>;
};

export default AwsNetworksPage;
