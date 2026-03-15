import React from 'react';
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import {BlocksIcon, Share2Icon} from "lucide-react";
import {Badge} from "@/components/ui/badge.tsx";
import AppStackProvider from "@/app/app-stacks/components/app-stack-provider.tsx";
import {InventoryItem} from "@/features/inventory/inventory.types.ts";
import {Link} from "react-router";

const AppStacksGrid = () => {
    const {items} = useInventory()

    const handleItemClick = (item: any) => {
        // Implement the logic to handle item click, e.g., open a modal or navigate
        console.log("Item clicked:", item);
    }

    return (
        <div>
            <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-1">
                {items && items.length > 0 && items.map((item: InventoryItem<any>) => (
                    <li
                        key={item.id}
                        className="rounded-lg border p-4 hover:shadow-md"
                    >
                        <AppStackProvider stack={item}>
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="mb-1 font-semibold flex space-x-2">
                                        <BlocksIcon/> <Link to={`/stacks/details/${item.id}`}>{item.id}</Link>
                                    </h2>
                                    <div className={"text-sm"}>
                                        {item?.properties?.repository?.url}
                                    </div>
                                    <div className={"text-muted-foreground text-sm mb-1"}>
                                        {item?.properties?.type} - {item?.properties?.stackfile}
                                    </div>
                                </div>
                                <div className={"text-right"}>
                                    <div className="flex gap-1 line-clamp-2 text-gray-500 text-sm mb-1">
                                    <div className={"text-sm"}>{item?.properties?.domain_name}</div>
                                        <Badge variant={"outline"}>{item?.properties?.deployment_target}</Badge>
                                        <Badge variant={"default"}>NOT DEPLOYED</Badge>
                                    </div>
                                </div>
                            </div>
                        </AppStackProvider>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default AppStacksGrid;