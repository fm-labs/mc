import { AxiosRequestConfig } from "axios";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { TaskStatusResponse, TaskSubmissionResponse } from "@/features/tasks/tasks.types.ts";
import { buildApiHttpClient } from "@/lib/api-http-client.ts";


export const buildApiClient = (baseURL: string) => {

    const apiHttpClient = buildApiHttpClient(baseURL);

/////////// Basic HTTP Methods //////////////

    const get = async (url: string, config?: AxiosRequestConfig) => {
        return apiHttpClient.get(url, config).then(response => response.data);
    };

    const post = async (url: string, data?: any, config?: AxiosRequestConfig) => {
        return apiHttpClient.post(url, data, config).then(response => response.data);
    };


/////////// Auth //////////////

    const authLogin = async (data: any, config?: AxiosRequestConfig) => {
        return apiHttpClient.post("api/auth/login", data, config).then(response => response.data);
    };

    const authLoginFormData = async (formData: FormData, config?: AxiosRequestConfig) => {
        return apiHttpClient.post("api/auth/login", formData, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            ...config,
        }).then(response => response.data);
    };

    const authLogout = async (config?: AxiosRequestConfig) => {
        return apiHttpClient.post("api/auth/logout", {}, config).then(response => response.data);
    };

// const authRegister = (data: any, config?: AxiosRequestConfig) => {
//     return mcHttpClient.post('auth/register', data, config).then(response => response.data);
// }

/////////// Configuration & Integrations //////////////

    const getConfiguration = (config?: AxiosRequestConfig) => async (): Promise<any> => {
        const response = await apiHttpClient.get(`api/configuration`, config);
        return response.data;
    };

    const getConnectedAccounts = (config?: AxiosRequestConfig) => async (): Promise<any> => {
        const response = await apiHttpClient.get(`api/integrations`, config);
        return response.data;
    };

    const connectAccount = async (provider: string, data: any, config?: AxiosRequestConfig): Promise<any> => {
        const response = await apiHttpClient.post(`api/integrations/${provider}`, data, config);
        return response.data;
    };

/////////// Inventory //////////////

    const getInventoryItems = async (itemType: string, config?: AxiosRequestConfig): Promise<InventoryItem<any>> => {
        const response = await apiHttpClient.get(`api/inventory/${itemType}`, config);
        return response.data;
    };

    const createInventoryItem = async (itemType: string, item: InventoryItem<any>, config?: AxiosRequestConfig): Promise<InventoryItem<any>> => {
        const response = await apiHttpClient.post(`api/inventory/${itemType}`, item, config);
        return response.data;
    };

    const getInventoryItem = async (itemType: string, itemId: string, config?: AxiosRequestConfig): Promise<InventoryItem<any>> => {
        const response = await apiHttpClient.get(`api/inventory/${itemType}/${itemId}`, config);
        return response.data;
    };

    const updateInventoryItem = async (itemType: string, item: InventoryItem<any>, config?: AxiosRequestConfig): Promise<InventoryItem<any>> => {
        const response = await apiHttpClient.put(`api/inventory/${itemType}/${item.id}`, item, config);
        return response.data;
    };

    const deleteInventoryItem = async (itemType: string, item: InventoryItem<any>, config?: AxiosRequestConfig): Promise<any> => {
        const response = await apiHttpClient.delete(`api/inventory/${itemType}/${item.id}`, config);
        return response.data;
    };
    const submitInventoryItemAction = async (itemType: string, item: InventoryItem<any>, action_name: string, action_args?: any, config?: AxiosRequestConfig): Promise<TaskSubmissionResponse> => {
        const response = await apiHttpClient.post(`api/inventory/${itemType}/${item.id}/action/${action_name}`, action_args || {}, config);
        return response.data;
    };


    /**
     * @deprecated Use submitInventoryItemAction with action_name 'scan' instead
     */
    const createInventoryScan = (config?: AxiosRequestConfig) => async (item: InventoryItem<any>): Promise<any> => {
        const response = await apiHttpClient.post(`api/inventory/${item.type}/${item.id}/action/scan`, {}, config);
        return response.data;
    };

    /**
     * @deprecated Use submitInventoryItemAction with itemType 'dns-domain' instead
     */
    const submitDomainAction = (config?: AxiosRequestConfig) => async (item: InventoryItem<any>, action_name: string, action_args?: any): Promise<TaskSubmissionResponse> => {
        const response = await apiHttpClient.post(`api/inventory/dns-domain/${item.id}/action/${action_name}`, action_args || {}, config);
        return response.data;
    };


/////////// Findings //////////////

    const getFindings = async (filters: any, config?: AxiosRequestConfig): Promise<any> => {
        const queryParams = new URLSearchParams(filters).toString();
        if (queryParams) {
            config = {
                ...config,
                params: {
                    ...config?.params,
                    ...filters,
                },
            };
        }
        const response = await apiHttpClient.get(`api/findings`, config);
        return response.data;
    };

//////////// XScans //////////////

    const createScan = (config?: AxiosRequestConfig) => async (data: any): Promise<any> => {
        //const response = await mcHttpClient.post(`api/xscan/run/`, data, config);
        const response = await apiHttpClient.post(`api/xscan/scan`, data, config);
        return response.data;
    };

    const getScanResults = (config?: AxiosRequestConfig) => async (scanId: string): Promise<any> => {
        const response = await apiHttpClient.get(`api/xscan/results/${scanId}`, config);
        return response.data;
    };

/////////// Tasks //////////////


    const submitCeleryTask = async (data?: any, config?: AxiosRequestConfig): Promise<any> => {
        const response = await apiHttpClient.post(`api/celery/tasks`, data || {}, config);
        return response.data;
    };


    const getCeleryTaskStatus = async (taskId: string, config?: AxiosRequestConfig): Promise<TaskStatusResponse> => {
        const response = await apiHttpClient.get(`api/celery/tasks/${taskId}`, config);
        return response.data;
    };


/////////// Tools //////////////

    const getToolList = async (config?: AxiosRequestConfig): Promise<Tool[]> => {
        const response = await apiHttpClient.get<ToolIndex>(`api/tools`, config);
        return Object.values(response.data || {});
    };

    const getTool = async (tool_name: string, config?: AxiosRequestConfig): Promise<Tool> => {
        const response = await apiHttpClient.get(`api/tools/${tool_name}`, config);
        return response.data;
    };

    const execTool = async (tool_name: string, params?: any, config?: AxiosRequestConfig): Promise<ToolExecResult> => {
        const response = await apiHttpClient.post(`api/tools/${tool_name}`, params || {}, config);
        return response.data;
    };

    /**
     * Run a tool and stream its output (ndjson). Resolves when the stream ends.
     */
    const execToolStream = async (
        tool_name: string,
        params: any,
        onEvent: (event: ToolStreamEvent) => void,
        signal?: AbortSignal,
    ): Promise<void> => {
        const token = localStorage.getItem("authToken");
        const url = new URL(`api/tools/${tool_name}/stream?format=json`, new URL(baseURL, window.location.href));
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Accept": "application/x-ndjson",
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            },
            body: JSON.stringify(params || {}),
            signal,
        });
        if (!response.ok || !response.body) {
            throw new Error(`Stream failed: ${response.status} ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        const emit = (line: string) => {
            if (!line.trim()) return;
            try {
                onEvent(JSON.parse(line));
            } catch {
                onEvent({ event: "STDOUT", data: line });
            }
        };
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";
            lines.forEach(emit);
        }
        emit(buffer + decoder.decode());
    };

    return {
        // Basic HTTP Methods
        get, post,
        // Auth
        authLogin, authLoginFormData, authLogout,
        // Configuration & Integrations
        getConfiguration,
        getConnectedAccounts,
        connectAccount,
        // Inventory
        getInventoryItems,
        getInventoryItem,
        createInventoryItem,
        updateInventoryItem,
        deleteInventoryItem,
        submitInventoryItemAction,
        submitDomainAction,
        createInventoryScan,
        // Findings
        getFindings,
        // XScans
        createScan,
        getScanResults,
        // Tasks
        submitCeleryTask,
        getCeleryTaskStatus,
        // Tools
        getToolList,
        getTool,
        execTool,
        execToolStream,
    };


};

