import React from "react";
import { Trash2Icon } from "lucide-react";
import { toast } from "react-toastify";
import { useApi } from "@/context/api-context.tsx";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { Button } from "@/components/ui/button.tsx";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog.tsx";

type InventoryDeleteProps = {
    itemType: string
    item: InventoryItem<any>
    onDeleted?: () => void
}

/**
 * Confirm dialog that deletes the item.
 * Calls onDeleted after the item was deleted.
 */
export const InventoryDeleteDialog = ({ itemType, item, onDeleted, open, onOpenChange }: InventoryDeleteProps & {
    open: boolean
    onOpenChange: (open: boolean) => void
}) => {
    const { api } = useApi();
    const [deleting, setDeleting] = React.useState<boolean>(false);

    const handleDelete = async () => {
        setDeleting(true);
        try {
            await api.deleteInventoryItem(itemType, item);
            toast.success(`Deleted ${itemType} "${item.id}"`);
            onOpenChange(false);
            onDeleted?.();
        } catch (error: any) {
            console.error("Error deleting item:", error);
            toast.error(`Error deleting "${item.id}": ${error?.response?.data?.detail || error?.message || "Unknown error"}`);
        } finally {
            setDeleting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !deleting && onOpenChange(v)}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Delete {itemType} "{item.id}"?</DialogTitle>
                    <DialogDescription>This removes the item from the inventory and can't be undone.</DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <DialogClose asChild>
                        <Button variant={"outline"} disabled={deleting}>Cancel</Button>
                    </DialogClose>
                    <Button variant={"destructive"} onClick={handleDelete} disabled={deleting}>
                        {deleting ? "Deleting..." : "Delete"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

/**
 * Delete button with a confirm dialog.
 */
const InventoryDeleteButton = (props: InventoryDeleteProps) => {
    const [open, setOpen] = React.useState<boolean>(false);

    return (
        <>
            <Button size={"sm"} variant={"destructive"} onClick={() => setOpen(true)}>
                <Trash2Icon size={14} /> Delete
            </Button>
            <InventoryDeleteDialog {...props} open={open} onOpenChange={setOpen} />
        </>
    );
};

export default InventoryDeleteButton;
