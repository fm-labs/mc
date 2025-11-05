import React from "react";
import { useAwsInventory } from "@/app/aws/aws-inventory-provider.tsx";
import { MultiSelect, MultiSelectProps } from "@/components/multi-select.tsx";

const AwsInventoryFilterbar = () => {
    const { items } = useAwsInventory();

    // const [filter, setFilter] = React.useState<AwsInventoryFilter>({
    //     accountIds: [],
    //     regionIds: [],
    //     serviceIds: [],
    //     resourceTypes: [],
    // })

    // const [selectedAccountIds, setSelectedAccountIds] = React.useState<string[]>([])
    // const [selectedRegionIds, setSelectedRegionIds] = React.useState<string[]>([])
    // const [selectedServiceIds, setSelectedServiceIds] = React.useState<string[]>([])
    // const [selectedResourceTypes, setSelectedResourceTypes] = React.useState<string[]>([])

    // React.useEffect(() => {
    //     const newSelection = {
    //         accountIds: selectedAccountIds,
    //         regionIds: selectedRegionIds,
    //         serviceIds: selectedServiceIds,
    //         resourceTypes: selectedResourceTypes,
    //     }
    //     console.log('FILTER:CHANGED', newSelection)
    //     setFilter(newSelection)
    // }, [selectedAccountIds, selectedRegionIds, selectedResourceTypes, selectedServiceIds])

    const availableAccountOptions: Array<{value: string, label: string}> = React.useMemo(() => {
        const accountIdSet = new Set<string>();
        items.forEach(item => {
            if (item.accountId) {
                accountIdSet.add(item.accountId);
            }
        });
        return Array.from(accountIdSet).map(accountId => ({ value: accountId, label: accountId }));
    }, [items]);

    const availableRegionOptions: Array<{value: string, label: string}> = React.useMemo(() => {
        const regionIdSet = new Set<string>();
        items.forEach(item => {
            if (item.region) {
                regionIdSet.add(item.region);
            }
        });
        return Array.from(regionIdSet).map(regionId => ({ value: regionId, label: regionId }));
    }, [items]);

    const availableServiceOptions: Array<{value: string, label: string}> = React.useMemo(() => {
        const serviceIdSet = new Set<string>();
        items.forEach(item => {
            if (item.serviceId) {
                serviceIdSet.add(item.serviceId);
            }
        });
        return Array.from(serviceIdSet).map(serviceId => ({ value: serviceId, label: serviceId }));
    }, [items]);

    const availableResourceTypeOptions: Array<{value: string, label: string}> = React.useMemo(() => {
        const resourceTypeSet = new Set<string>();
        items.forEach(item => {
            if (item.resourceType) {
                resourceTypeSet.add(item.resourceType);
            }
        });
        return Array.from(resourceTypeSet).map(resourceType => ({ value: resourceType, label: resourceType }));
    }, [items]);

    console.log("Available Account Options:", availableAccountOptions);

    const selectProps: Partial<MultiSelectProps> = {
        minWidth: "200px",
        maxWidth: "300px",
        responsive: false,
        maxCount: 5,
        singleLine: true,
        autoSize: false,
    }

    return (
        <div>
            <div>
                Filters
            </div>
            {/** Select box for Account IDs */}
            <div className={"flex flex-row gap-2 flex-wrap"}>
                <MultiSelect options={availableAccountOptions} onValueChange={console.log} placeholder={"Select Accounts"} {...selectProps} />
                <MultiSelect options={availableRegionOptions} onValueChange={console.log} placeholder={"Select Regions"} {...selectProps} />
                <MultiSelect options={availableServiceOptions} onValueChange={console.log} placeholder={"Select Services"} {...selectProps} />
                <MultiSelect options={availableResourceTypeOptions} onValueChange={console.log} placeholder={"Select Resources"} {...selectProps} />
            </div>
        </div>
    );
};

export default AwsInventoryFilterbar;
