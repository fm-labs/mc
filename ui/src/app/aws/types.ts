
export type AwsInventoryItemFull = {
    id: string;
    arn: string;
    accountId: string;
    region: string;
    serviceId: string;
    resourceType: string;
    resourceTypeLabel: string;
    name: string;
    properties: { [key: string]: any };
    tags?: { [key: string]: string };
    [key: string]: any; // for any additional properties
}


export interface AwsInventoryFilter {
    accountIds: string[]
    regionIds: string[]
    serviceIds: string[]
    resourceTypes: string[]
    properties?: { [key: string]: any } // for additional filtering based on properties
}
