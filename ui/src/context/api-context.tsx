import React from "react";
import { buildApiClient } from "@/lib/api-client.ts";
import {MC_API_BASE_URL} from "@/constants.ts";

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


export const useApi = () => {
    const context = React.useContext(ApiContext);
    if (context === undefined) {
        throw new Error("useApi must be used within an ApiProvider");
    }
    return context;
}
