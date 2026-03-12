import React from "react";
import { Badge } from "@/components/ui/badge.tsx";
import { showDataToast } from "@/utils/show-data-toast.tsx";
import { useAwsInventory } from "@/app/aws/aws-inventory-provider.tsx";
import { formatDistanceToNow } from "date-fns";
import { AwsInventoryItemFull } from "@/app/aws/types.ts";
import AwsInventoryItem from "@/app/aws/components/aws-inventory-item.tsx";
import Header from "@/components/header.tsx";
import { Button } from "@/components/ui/button.tsx";
import { useNavigate } from "react-router";
import { useApi } from "@/context/api-context.tsx";
import GraphVisualization from "@/app/aws/components/graph-visualization.tsx";

const AwsInventory = () => {
    const { items: data, fetchItems } = useAwsInventory();
    const { api } = useApi();
    const navigate = useNavigate();
    const [view, _setView] = React.useState<"list" | "grid">("list");
    const [activeItem, setActiveItem] = React.useState<AwsInventoryItemFull | null>(null);
    const [activeIndex, setActiveIndex] = React.useState<number | null>(null);

    const [awsgraph, setAwsGraph] = React.useState<any>(null);

    const handleOnItemClick = (idx: number) => () => {
        if (idx < 0 || idx >= data.length) return;
        const item = data[idx];
        console.log("Item clicked:", item);
        //alert(JSON.stringify(item, null, 2));
        showDataToast(item, `Item ${item?.name || item?.id || idx}`); // Use name or id as title
        setActiveIndex(idx);
        setActiveItem(item);
        fetchItemGraph(item);
    };

    const fetchItemGraph = async (item: AwsInventoryItemFull) => {
        try {
            //const response = await fetch(`/api/aws/inventory/item-graph?accountId=${item.accountId}&regionId=${item.regionId}&serviceId=${item.serviceId}&resourceType=${item.resourceType}&resourceId=${item.resourceId}`);
            const response = await api.get(`/api/aws/inventory/item-graph?id=${item?._id}`);
            const graphData = response
            console.log("Fetched item graph data:", graphData);
            // Handle the graph data as needed
            setAwsGraph(graphData);
        } catch (error) {
            console.error("Failed to fetch item graph:", error);
        }
    }

    const containerClassName = view==="grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-1":"";
    const itemClassName = view==="grid" ? "flex flex-col":"border p-1 mb-1";

    return (
        <div>

            <Header title={"AWS Inventory"} subtitle={"All resources from all accounts"}>
                <span>
                    <Button className="btn-primary btn" onClick={() => navigate("networks")}>Network</Button>
                    <Button className="btn-primary btn" onClick={() => fetchItems()}>Refresh</Button>
                </span>
            </Header>
            {data && data.length > 0 ? (
                <ul className={containerClassName}>
                    {data.map((item, idx) => (
                        <li key={idx}>
                            <div className={itemClassName}>
                                <Badge variant="secondary" className={"ml-2"}>{item.accountId}</Badge>
                                <Badge variant="secondary" className={"ml-2"}>{item.regionId}</Badge>
                                <Badge variant="secondary" className={"ml-2"}>{item.serviceId}</Badge>
                                <Badge variant="secondary" className={"ml-2"}>{item.resourceType}</Badge>
                                <Badge variant="secondary" className={"ml-2"}
                                       onClick={handleOnItemClick(idx)}>{item.name}</Badge>
                                <span
                                    className={"text-xs text-muted-foreground ml-2"}>updated {formatDistanceToNow(item.updated)} ago</span>
                            </div>
                            <div>
                                {activeItem && activeIndex===idx && (
                                    <>
                                        {awsgraph && <GraphVisualization data={awsgraph as any} />}
                                        <AwsInventoryItem item={activeItem} />
                                    </>

                                )}
                            </div>
                        </li>
                    ))}
                </ul>
            ):(
                <p>No items found.</p>
            )}
        </div>
    );
};

export default AwsInventory;
