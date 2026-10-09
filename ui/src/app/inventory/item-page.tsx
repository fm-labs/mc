import { Link, useLoaderData, useNavigate, useParams } from "react-router";
import { ArrowLeftIcon, PencilIcon } from "lucide-react";
import ReactJson from "@microlink/react-json-view";
import { InventoryProvider, useInventory } from "@/app/inventory/components/inventory-provider.tsx";
import InventoryItemActionButtons from "@/app/inventory/components/inventory-item-action-buttons.tsx";
import InventoryDeleteButton from "@/app/inventory/components/inventory-delete-button.tsx";
import InventoryItemProperties from "@/app/inventory/components/inventory-item-properties.tsx";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible.tsx";
import { ucFirst } from "@/utils/textutil.ts";


const InventoryItemPage = () => {
    const item = useLoaderData() as InventoryItem<any> | null;
    const { itemType, itemId } = useParams<{ itemType: string, itemId: string }>();

    if (!itemType) {
        return <p className="text-center">Item type is not specified.</p>;
    }
    if (!item) {
        return (
            <MainContent>
                <p className="text-center">Item "{itemId}" not found in {itemType} inventory.</p>
                <BackLink itemType={itemType} />
            </MainContent>
        );
    }

    return (
        // key: reset the provider state when navigating to another item
        <InventoryProvider itemType={itemType} item={item} key={`${itemType}/${item.id}`}>
            <InventoryItemDetails />
        </InventoryProvider>
    );
};


const InventoryItemDetails = () => {
    const { itemType, inputSchema, currentItem, setOpen } = useInventory<Record<string, any>>();
    const navigate = useNavigate();

    if (!currentItem) {
        return null;
    }

    // the id is shown in the header
    const { id: _id, ...properties } = currentItem.properties || {};
    const label = properties.label || properties.name || properties.title;
    const typeTitle = inputSchema?.title || ucFirst(itemType);

    return (
        <MainContent>
            <BackLink itemType={itemType} title={typeTitle} />
            <Header
                title={label || currentItem.id}
                subtitle={label ? `${typeTitle} · ${currentItem.id}` : typeTitle}>
                <div className="flex flex-wrap items-center gap-1">
                    <Button size={"sm"} onClick={() => setOpen("update")}>
                        <PencilIcon size={14} /> Edit
                    </Button>
                    <InventoryItemActionButtons item={currentItem} />
                    <InventoryDeleteButton itemType={itemType} item={currentItem}
                                           onDeleted={() => navigate(`/admin/inventory/${itemType}`)} />
                </div>
            </Header>

            <SectionCard title={"Properties"}>
                <InventoryItemProperties data={properties} schema={inputSchema as any} />
            </SectionCard>

            <Collapsible>
                <CollapsibleTrigger asChild>
                    <Button variant={"link"} size={"sm"} className={"px-0"}>Show raw JSON</Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <div className="overflow-auto rounded-md border p-2">
                        <ReactJson src={currentItem} name={false} displayDataTypes={false} enableClipboard={true} />
                    </div>
                </CollapsibleContent>
            </Collapsible>
        </MainContent>
    );
};


const BackLink = ({ itemType, title }: { itemType: string, title?: string }) => (
    <Link to={`/admin/inventory/${itemType}`}
          className="inline-flex w-fit items-center gap-1 text-sm text-muted-foreground hover:underline">
        <ArrowLeftIcon size={14} /> {title || ucFirst(itemType)}
    </Link>
);

export default InventoryItemPage;
