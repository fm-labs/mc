import { DataTableGeneric } from "@/components/data-table/data-table-generic.tsx";
import { useLoaderData } from "react-router";
import { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge.tsx";
import {
    DropdownMenuItem, DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu.tsx";
import DropdownMenuDots from "@/components/dropdown-menu-dots.tsx";

type Cloud = {
    name: string;
    platform: string;
}

export default function CloudsPage() {
    const data = useLoaderData();

    console.log(data);

    const columns: ColumnDef<Cloud>[] = [
        {
            accessorKey: "name",
            header: "Cloud name",
            cell: ({ row }) => (
                <div className="w-32">
                    <Badge variant="outline" className="text-muted-foreground px-1.5">
                        {row.original.name}
                    </Badge>
                </div>
            ),
        },
        {
            accessorKey: "platform",
            header: "Cloud Platform",
            cell: ({ row }) => (
                <div className="w-32">
                    <Badge variant="outline" className="text-muted-foreground px-1.5">
                        {row.original.platform}
                    </Badge>
                </div>
            ),
        },
        {
            id: "actions",
            cell: () => (
                <DropdownMenuDots>
                    <DropdownMenuItem>Edit</DropdownMenuItem>
                    <DropdownMenuItem>Make a copy</DropdownMenuItem>
                    <DropdownMenuItem>Favorite</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem variant="destructive">Delete</DropdownMenuItem>
                </DropdownMenuDots>
            ),
        },
    ];

    return (
        <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
            {data ? <DataTableGeneric columns={columns} data={data} />:<p className="text-center">No clouds found.</p>}
        </div>
    );
}
