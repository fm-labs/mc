export type TaskSubmissionResponse = {
    task_id: string;
    status?: string;
    result?: any;
    error?: string;
}

export type TaskStatusResponse = {
    task_id: string;
    state?: string;
    result?: any;
    progress?: {
        current: number;
        total: number;
        status?: string;
    };
    error?: string;
}
