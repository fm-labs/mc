import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {ColumnDef} from "@tanstack/react-table";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import Data from "@/components/data.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";
import {autoColumnsFromData} from "@/components/data-table/data-table-helper.tsx";

const DockerHostNetworks = () => {
    const {fetchContainerData} = useContainerHost()
    const [networks, setNetworks] = React.useState<any[]>()

    // const networks = React.useMemo(() => {
    //     console.log("Networks summary:", summary)
    //     return []
    // }, [summary])


    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            accessorKey: "Name",
            header: "Name",
            cell: ({row}) => (
                <div className={`font-bold`} title={row.original.Name}>
                    <Data data={row.original}/>{' '}{row.original?.Name || "<none>"}
                </div>
            ),
        },
        {
            accessorKey: "Id",
            header: "Id",
        },
        {
            accessorKey: "Scope",
            header: "Scope",
        },
        {
            accessorKey: "Driver",
            header: "Driver",
        },
        {
            accessorKey: "EnableIPv4",
        },
        {
            accessorKey: "EnableIPv6",
        },
        {
            accessorKey: "Internal",
        },
        {
            accessorKey: "Created",
            header: "Created",
            cell: ({row}) => (
                <div className="text-right">
                    {row.original?.Created}
                </div>
            ),

        },
    ], []);

    React.useEffect(() => {
        const loadNetworks = async () => {
            const data = await fetchContainerData("networks")
            setNetworks(data)
        }
        loadNetworks()
    }, [])

    return (
        <div>
            <DockerHostHeader title={"Networks"}/>

            {networks === undefined && <p>Loading networks...</p>}
            {!networks || networks?.length === 0 ? (
                <p>No networks found.</p>
            ) : (
                <DataTableGeneric columns={columns} data={networks}/>
            )}
        </div>
    );
};

export default DockerHostNetworks;