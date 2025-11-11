import React from 'react';
import {useInventory} from "@/app/inventory/components/inventory-provider.tsx";
import {Share2Icon} from "lucide-react";
import {Badge} from "@/components/ui/badge.tsx";
import AppStackProvider from "@/app/app-stacks/components/app-stack-provider.tsx";
import {InventoryItem} from "@/features/inventory/inventory.types.ts";
import {Link} from "react-router";

const AppStacksGrid = () => {
    const { items } = useInventory()
    
    const handleItemClick = (item: any) => {
        // Implement the logic to handle item click, e.g., open a modal or navigate
        console.log("Item clicked:", item);
    }

    return (
        <div>
            <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {items && items.length > 0 && items.map((item: InventoryItem<any>) => (
                    <li
                        key={item.name}
                        className="rounded-lg border p-4 hover:shadow-md"
                    >
                        <AppStackProvider stack={item}>
                            <div className="mb-4 flex items-center justify-between">
                                <div
                                    className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
                                    onClick={() => handleItemClick(item)}
                                >
                                    <Share2Icon />
                                </div>
                                <div>
                                    {/*<Button
                                        variant="outline"
                                        size="sm"
                                        //onClick={() => setCurrentItem(item, null)}
                                        //className={`${item.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                                    >
                                        Add Host
                                    </Button>*/}{" "}
                                    {/*<Button
                                        variant="outline"
                                        size="sm"
                                        //onClick={() => setCurrentItem(item, null)}
                                        //className={`${item.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                                    >
                                        Launch new Host
                                    </Button>*/}
                                </div>
                            </div>
                            <div>
                                <h2 className="mb-1 font-semibold">
                                    <Link to={`/stacks/details/${item.item_key}`}>{item.name}</Link>
                                </h2>
                                <div className={"text-muted-foreground text-sm mb-1"}>
                                    {item?.properties?.template_repository}<br />
                                    {item?.properties?.template_stackfile}
                                </div>
                                <div className="flex gap-1 line-clamp-2 text-gray-500 text-sm mb-1">
                                    <Badge variant={"outline"}>{item?.properties?.container_host}</Badge>
                                    <Badge variant={"default"}>DEPLOYED</Badge>
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