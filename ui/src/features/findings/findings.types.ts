

export type Finding = {
    resource_id: string;
    resource_type: string;
    resource_name?: string;
    check_name: string;
    severity: number;
    message?: string;
    category?: string;
    timestamp: number;
    first_seen: number;
}
