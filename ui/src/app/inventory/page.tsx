import { useLoaderData, useParams } from "react-router";
import { InventoryProvider } from "@/app/inventory/components/inventory-provider.tsx";
import { InventoryPrimaryButtons } from "@/app/inventory/components/inventory-primary-buttons.tsx";
import { ucFirst } from "@/utils/textutil.ts";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import InventoryDataTable from "@/app/inventory/components/inventory-data-table.tsx";
import DevOnly from "@/components/dev-only.tsx";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";
import React from "react";
import InventorySchemaForm from "@/app/inventory/components/inventory-schema-form.tsx";


const InventoryPage = () => {
    const data = useLoaderData();
    const { itemType } = useParams<{ itemType: string }>();

    // const columns = React.useMemo(() => {
    //     const dataColumns = autoColumnsFromData(data as any[]);
    //     const actionsColumn =
    //         {
    //             id: "actions",
    //             accessorKey: "_actions_",
    //             header: "Actions",
    //             cell: ({ row }: { row: any}) => <DataTableRowActions row={row} actions={actions} />,
    //         }
    //     return [...dataColumns, actionsColumn];
    // }, [data, actions])


    if (!itemType) {
        return <p className="text-center">Item type is not specified.</p>;
    }
    if (!data) {
        return <p className="text-center">No data available for {itemType}.</p>;
    }

    return (
        <InventoryProvider itemType={itemType} data={data as any[]}>
            <MainContent>
                <Header
                    title={`${ucFirst(itemType)} Inventory`}
                    subtitle={`Manage your ${itemType} items here.`}>
                    <InventoryPrimaryButtons />
                </Header>
                {/*<InventorySchemaForm />*/}
                <InventoryDataTable />
                <DevOnly>
                    <hr />
                    {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
                </DevOnly>
            </MainContent>
        </InventoryProvider>
    );
};

export default InventoryPage;
