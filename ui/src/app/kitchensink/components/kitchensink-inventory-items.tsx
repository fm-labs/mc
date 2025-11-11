import React from "react";

import Data from "@/components/data.tsx";
import { InventoryMutateDrawer } from "@/app/inventory/components/inventory-mutate-drawer.tsx";
import { getWidgetComponent } from "@/app/kitchensink/components/kitchensink-widgets.tsx";
import { getItemTypeWidgets } from "@/app/kitchensink/components/data/items.tsx";
import { InventoryActionDef } from "@/features/inventory/inventory.types.ts";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";


const Item = ({ item, onClick }: { item: any, isActive: boolean, onClick: () => void }) => {
    const itemType = item.item_type;
    //const views = getItemTypeViews(itemType);
    const widgets = getItemTypeWidgets(itemType);
    const [isActive, _setIsActive] = React.useState(true);

    const { metadata, setDialog, handleAction } = useInventory();

    const handleActionClick = (action: InventoryActionDef) => (item: any) => {
        console.log(`Action "${action}" clicked for item:`, item);
        handleAction(action)(item);
    };

    const handleEditItemClick = () => {
        console.log(`Create new item of type: ${itemType}`);
        const formProps = {
            open: true,
            onOpenChange: (open: boolean) => {
                if (!open) {
                    setDialog(null);
                }
            },
            currentRow: item,
        }
        const form = <InventoryMutateDrawer {...formProps} />
        setDialog(form);
    }

    // const handleViewClick = (view: string) => () => {
    //     console.log(`View "${view}" clicked for item:`, item);
    //     // Implement view handling logic here
    //     toast.info("View: " + view);
    // };

    // React.useEffect(() => {
    //     setCurrentItem(item)
    // }, [item])

    return (<li className={`break-inside-avoid border-b-1 ${isActive ? 'bg-gray-100 dark:bg-gray-600 border-l-4 border-lime-500' : ''}`}>
        <div className={`hover:underline cursor-pointer ${isActive ? 'font-bold text-lime-500' : ''}`}
             onClick={onClick}>{item.name}
        </div>
        {isActive
            && <div
                className={""}>
                {/*<pre>{JSON.stringify(item, null, 2)}</pre>*/}
                <div className={"flex flex-wrap items-center space-x-2"}>
                    <Data asButton={false} data={item} />
                    <span className={"cursor-pointer hover:underline"} onClick={handleEditItemClick}>Edit</span>

                    {metadata?.actions && metadata?.actions
                        .filter(action => action.id).map(action => (
                        <span key={action.id} className={"cursor-pointer text-orange-300 hover:underline"}
                              title={action.name}
                              onClick={() => handleActionClick(action)(item)}>{action.id}</span>
                    ))}
                    {/*views && getItemTypeViews(itemType).map(view => (
                        <span key={view} className={"cursor-pointer mr-2 text-blue-300 hover:underline"}
                              onClick={handleViewClick(view)}>[{view}]</span>
                    ))*/}
                </div>
                {widgets && <div className={""}>
                    {getItemTypeWidgets(itemType).map((widgetType) => {
                        const WidgetComponent: React.FC<any> = getWidgetComponent(widgetType);
                        return <div key={widgetType}
                                    className={"_border-1 _border-gray-700 _bg-gray-900 overflow-scroll max-h-[142px]"}>
                            <WidgetComponent item={item} widgetType={widgetType} />
                        </div>;
                    })}
                </div>}
            </div>}
    </li>);
};

const KitchensinkInventoryItems = () => {
    const { itemType, items, setDialog } = useInventory()
    const [activeItemKey, setActiveItemKey] = React.useState<string | null>(null);

    const toggleActiveItem = (item_key: string) => {
        if (activeItemKey===item_key) {
            setActiveItemKey(null);
        } else {
            setActiveItemKey(item_key);
        }
    };

    const handleCreateItemClick = (itemType: string) => () => {
        console.log(`Create new item of type: ${itemType}`);
        const formProps = {
            open: true,
            onOpenChange: (open: boolean) => {
                if (!open) {
                    setDialog(null);
                }
            }
        }
        const form = <InventoryMutateDrawer {...formProps} />
        setDialog(form);
    }

    return (
        <div className={"text-xs m-0 p-0"}>
            <div>
                <span className={"font-bold underline"}>{itemType}</span>{" "}
                <span onClick={handleCreateItemClick(itemType)}>[+]</span>
            </div>
            {items && items.length > 0 ? (
                <ul className={"_sm:columns-1 _md:columns-1 _lg:columns-1 _xl:columns-3 gap-2"}>
                    {items.map((item) => (
                        <Item key={item.item_key}
                              item={item}
                              onClick={() => toggleActiveItem(item.item_key)}
                              isActive={activeItemKey===item.item_key} />
                    ))}
                </ul>
            ):(
                <p>No items found.</p>
            )}
            {/*{activeItemKey && <InventoryMutateDrawer open={true}
                                                      onOpenChange={() => setActiveItemKey(null)}
                                                      currentRow={items.find(i => i.item_key === activeItemKey)} />}

            {activeItemKey === "__NEW__" && <InventoryMutateDrawer open={true}
                                                                    onOpenChange={() => setActiveItemKey(null)}
                                                                    currentRow={undefined} />}*/}
        </div>
    );
};

export default KitchensinkInventoryItems;
