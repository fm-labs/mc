import { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge.tsx";
import { DataTableRowAction, DataTableRowActions } from "@/components/data-table/data-table-generic.tsx";
import { Finding } from "@/features/findings/findings.types.ts";
import { formatDistanceToNow } from "date-fns";


const SeverityBadge = ({ severity }: { severity: number }) => {
    let colorClass;
    let text;
    switch (severity) {
        case 4:
            text = "CRITICAL";
            colorClass = "text-red-700";
            break;
        case 3:
            text = "HIGH";
            colorClass = "text-red-400";
            break;
        case 2:
            text = "MEDIUM";
            colorClass = "text-yellow-400";
            break;
        case 1:
            text = "LOW";
            colorClass = "text-blue-400";
            break;
        case 0:
        default:
            text = "INFO";
            colorClass = "text-gray-400";
            break;
    }
    return (
        <Badge variant="outline" className={`px-1.5 ${colorClass}`}>
            {text}
        </Badge>
    );
}


const actions: DataTableRowAction[] = [
    // {
    //     name: "Edit",
    //     href: "#",
    //     handler: (item: Finding, action: DataTableRowAction) => alert(`Action ${action.name} clicked for ${item.check_name}`),
    // },
    // {
    //     name: "Scan",
    //     href: "#",
    //     handler: (item: Finding<any>) => createInventoryScan()(item)
    //         .then(data => console.log(data)),
    // },
    // { name: "Enable scanning", href: "#" },
    // { name: "Favorite", href: "#" },
    // { name: "__SEPARATOR__" },
    // { name: "Delete", href: "#", variant: "destructive" },
];

export const findingsTableColumns: ColumnDef<Finding>[] = [
    {
        accessorKey: "severity",
        header: "Severity",
        cell: ({ row }) => (
            <div className="">
                <SeverityBadge severity={row.original.severity} />
            </div>
        ),
    },
    {
        accessorKey: "check_name",
        header: "Check name",
        cell: ({ row }) => (
            <div className="">
                <Badge variant="outline" className="text-muted-foreground px-1.5">
                    {row.original.check_name}
                </Badge>
            </div>
        ),
    },
    {
        accessorKey: "resource_type",
        header: "Resource Type",
        cell: ({ row }) => (
            <div className="">
                <Badge variant="outline" className="text-muted-foreground px-1.5">
                    {row.original?.resource_type || "unknown"}
                </Badge>
            </div>
        ),
    },
    // {
    //     accessorKey: "resource_id",
    //     header: "Resource Id",
    //     cell: ({ row }) => (
    //         <div className="">
    //             {row.original?.resource_id || "unknown"}
    //         </div>
    //     ),
    // },
    {
        accessorKey: "resource_name",
        header: "Resource Name",
        cell: ({ row }) => (
            <div className="">
                {row.original?.resource_name || "unknown"}
            </div>
        ),
    },
    {
        accessorKey: "message",
        header: "Message",
        cell: ({ row }) => (
            <div className="">
                {row.original.message}
            </div>
        ),
    },
    {
        accessorKey: "timestamp",
        header: "Checked",
        cell: ({ row }) => (
            <div className="">
                {row.original.timestamp ? formatDistanceToNow(row.original.timestamp * 1000) + ' ago' : '?'}
            </div>
        ),
    },
    // {
    //     id: "_findings",
    //     header: "Findings",
    //     cell: () => (
    //         <div className="">
    //             {/*<FindingsSummary target={`software-finding://${row.original.name}`} />*/}
    //             <Badge variant="outline" className="text-muted-foreground px-1.5 text-red-700">
    //                 0 CRIT
    //             </Badge>
    //             <Badge variant="outline" className="text-muted-foreground px-1.5 text-red-400">
    //                 0 HIGH
    //             </Badge>
    //             <Badge variant="outline" className="text-muted-foreground px-1.5 text-yellow-400">
    //                 0 MED
    //             </Badge>
    //             <Badge variant="outline" className="text-muted-foreground px-1.5 text-blue-400">
    //                 0 LOW
    //             </Badge>
    //             <Badge variant="outline" className="text-muted-foreground px-1.5 text-gray-400">
    //                 0 INFO
    //             </Badge>
    //         </div>
    //     ),
    // },
    {
        id: "actions",
        cell: ({ row }) => <DataTableRowActions row={row} actions={actions} />,
    },
];
