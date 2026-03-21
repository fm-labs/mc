import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {ColumnDef} from "@tanstack/react-table";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import Data from "@/components/data.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";

const DockerHostVolumes = () => {
    const { summary, fetchVolumes } = useContainerHost()
    //const [volumes, setVolumes] = React.useState<any[]>()
    const volumes = React.useMemo(() => {
        return summary?.Volumes
            .sort((a: any, b: any) => a.Name?.localeCompare(b.Name))
            .sort((a: any, b: any) => b?.UsageData?.RefCount - a?.UsageData?.RefCount) || []
    }, [summary])

    const columns: ColumnDef<any>[] = React.useMemo(() => [
    {
        accessorKey: "Name",
        header: "Name",
        cell: ({ row }) => (
            <div className={`font-bold ${row.original?.UsageData?.RefCount > 0 ? "text-green-500" : ""}`} title={row.original.Name}>
                {row.original?.Name || "<none>"}
                <Data data={row.original} />
            </div>
        ),
    },
    // {
    //     accessorKey: "Scope",
    //     header: "Scope",
    // },
    {
        accessorKey: "Driver",
        header: "Driver",
    },
    {
        accessorKey: "UsageData.RefCount",
        header: "Usage",
    },
    {
        accessorKey: "UsageData.Size",
        header: "Size",
            cell: ({row}) => (
                <div className="text-right">
                    {row.original?.UsageData?.Size ? (row.original?.UsageData?.Size / (1024 * 1024)).toFixed(2) + " MB" : "0 MB"}
                </div>
            ),
    },
    // {
    //     accessorKey: "Mountpoint",
    //     header: "Mountpoint",
    //     enableHiding: true
    // },
    {
        accessorKey: "CreatedAt",
        header: "CreatedAt",
            cell: ({row}) => (
                <div className="text-right">
                    {row.original?.CreatedAt}
                </div>
            ),

    },
    ], []);

    // React.useEffect(() => {
    //     const loadVolumes = async () => {
    //         const data = await fetchVolumes()
    //         setVolumes(data)
    //     }
    //     loadVolumes()
    // }, [fetchVolumes])

    if (volumes === undefined) {
        return <div>Loading volumes...</div>
    }

    return (
        <div>
            <DockerHostHeader title={"Volumes"}/>

            {volumes?.length === 0 ? (
                <p>No volumes found.</p>
            ) : (
                <DataTableGeneric columns={columns} data={volumes} />
            )}
        </div>
    );
};

export default DockerHostVolumes;