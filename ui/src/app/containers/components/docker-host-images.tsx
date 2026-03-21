import React from 'react';
import {useContainerHost} from "@/app/containers/components/container-host-provider.tsx";
import {DataTableGeneric} from "@/components/data-table/data-table-generic.tsx";
import {ColumnDef} from "@tanstack/react-table";
import Data from "@/components/data.tsx";
import Header from "@/components/header.tsx";
import { Button } from "@/components/ui/button";
import {RJSFSchema} from "@rjsf/utils";
import {SchemaFormDrawer} from "@/components/form/schema-form-drawer.tsx";
import DockerHostHeader from "@/app/containers/components/docker-host-header.tsx";

const pullImageSchema: RJSFSchema = {
    title: "Pull Container Image",
    type: "object",
    required: ["image"],
    properties: {
        image: {
            type: "string",
            title: "Image Name",
            description: "Enter the name of the Docker image to pull (e.g., 'nginx:latest')"
        }
    }
}


const DockerHostImagePull = () => {
    const {pullImage} = useContainerHost()
    const [dialogOpen, setDialogOpen] = React.useState(false)

    const handlePull = async (formData: any) => {
        console.log("Pulling image with data:", formData)
        const imageName = formData?.image || ""
        if (imageName.trim() === "") {
            alert("Please enter an image name");
            return;
        }
        try {
            await pullImage(imageName)
            alert(`Pulling image: ${imageName}`)
        } catch (error: any) {
            console.error("Error pulling image:", error)
            alert(`Error pulling image: ${error?.message || error}`)
        }
    }

    return (
        <div>
            <Button onClick={() => setDialogOpen(!dialogOpen)}>Pull Image</Button>

            <SchemaFormDrawer schema={pullImageSchema} open={dialogOpen}
                              onOpenChange={() => setDialogOpen(false)}
                              onSubmit={handlePull} />
        </div>

    )
}


const DockerHostImages = () => {
    const {fetchImages} = useContainerHost()
    const [images, setImages] = React.useState<any[]>()

    const columns: ColumnDef<any>[] = React.useMemo(() => [
        {
            accessorKey: "Id",
            header: "Image Id",
            cell: ({row}) => (
                <div className="font-bold" title={row.original.Id}>
                    <Data data={row.original} />{' '}{row.original.Id.substring(7, 19)}
                </div>
            ),
        },
        {
            accessorKey: "RepoTags",
            header: "Tags",
            cell: ({row}) => (
                <div className="">
                    {row.original?.RepoTags.join(", ") || "<none>"}
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
            <DockerHostHeader title={"Images"}>
                <DockerHostImagePull />
            </DockerHostHeader>
            {images?.length === 0 ? (
                <p>No images found.</p>
            ) : (
                <DataTableGeneric columns={columns} data={images}/>
            )}
        </div>
    );
};

export default DockerHostImages;