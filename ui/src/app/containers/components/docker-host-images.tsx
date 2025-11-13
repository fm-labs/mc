import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import {ColumnDef} from "@tanstack/react-table";
import Data from "@/components/data.tsx";

const DockerHostImages = () => {
    const {fetchImages} = useContainerHost()
    const [images, setImages] = React.useState<any[]>()

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            accessorKey: "Id",
            header: "Image Id",
            cell: ({row}) => (
                <div className="font-bold" title={row.original.Id}>
                    {row.original.Id.substring(7, 19)}
                </div>
            ),
        },
        {
            accessorKey: "RepoTags",
            header: "Tags",
            cell: ({row}) => (
                <div className="">
                    {row.original?.RepoTags.join(", ") || "<none>"}
                    <Data data={row.original} />
                </div>
            ),
        },
        {
            accessorKey: "Size",
            header: "Size",
            cell: ({row}) => (
                <div className="text-right">
                    {row.original?.Size ? (row.original.Size / (1024 * 1024)).toFixed(2) + " MB" : "0 MB"}
                </div>
            ),
        },
        {
            accessorKey: "Architecture",
            header: "Architecture",
        },
        {
            accessorKey: "Os",
            header: "Os",
        },
        {
            accessorKey: "Created",
            header: "Created",
            cell: ({row}) => (
                <div className="text-right">
                    {row.original?.Created}
                </div>
            ),
        }
    ], []);

    React.useEffect(() => {
        const loadImages = async () => {
            setImages(undefined)
            const data = await fetchImages()
            setImages(data)
        }
        loadImages()
    }, [fetchImages])

    if (images === undefined) {
        return <div>Loading images...</div>
    }

    return (
        <div>
            <h3 className={"font-bold text-lg"}>Images</h3>
            {images?.length === 0 ? (
                <p>No images found.</p>
            ) : (
                <DataTableGeneric columns={columns} data={images}/>
            )}
        </div>
    );
};

export default DockerHostImages;