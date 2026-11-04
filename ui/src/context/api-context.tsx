import React from "react";
import { buildApiClient } from "@/lib/api-client.ts";
import {MC_API_BASE_URL} from "@/constants.ts";
import { nodeHeaders } from "@/lib/node-headers.ts";

type ApiContextType = {
    apiBaseUrl: string,
    setApiBaseUrl: (url: string) => void,
    api: any
}

export const ApiContext = React.createContext<ApiContextType | undefined>(undefined);

export const ApiProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [apiBaseUrl, setApiBaseUrl] = React.useState<string>(/*localStorage.getItem("mc_api_base_url") ||*/ MC_API_BASE_URL);
    const api = React.useMemo(() => {
        return buildApiClient(apiBaseUrl);
    }, [apiBaseUrl]);

    // React.useEffect(() => {
    //     localStorage.setItem("mc_api_base_url", apiBaseUrl);
    // }, [apiBaseUrl]);

    // if (!apiBaseUrl) {
    //     return (<div style={{ padding: "2rem" }}>
    //         <h2>Set API Base URL</h2>
    //         <p>Please enter the base URL for the API to continue.</p>
    //         <input
    //             type="text"
    //             placeholder={""}
    //             value={apiBaseUrl}
    //             onChange={(e) => setApiBaseUrl(e.target.value)}
    //             className={"w-100 border rounded p-2"}
    //         />
    //     </div>
    //     );
    // }

    return (
        <ApiContext.Provider value={{ apiBaseUrl, setApiBaseUrl, api }}>
            {children}
        </ApiContext.Provider>
    );
}


/**
 * Scopes `useApi()` to a host: every request below it goes to that node through the node proxy
 * (x-mc-node header). The local mc ("localhost") gets the plain client.
 */
export const HostApiProvider: React.FC<{ hostId: string, children: React.ReactNode }> = ({ hostId, children }) => {
    const parent = useApi();
    const api = React.useMemo(
        () => buildApiClient(parent.apiBaseUrl, nodeHeaders(hostId)),
        [parent.apiBaseUrl, hostId],
    );

    return (
        <ApiContext.Provider value={{ ...parent, api }}>
            {children}
        </ApiContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useApi = () => {
    const context = React.useContext(ApiContext);
    if (context === undefined) {
        throw new Error("useApi must be used within an ApiProvider");
    }
    return context;
}
