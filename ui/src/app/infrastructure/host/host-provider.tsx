import React from "react";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import { useApi } from "@/context/api-context.tsx";
import { toast } from "sonner";


type HostContextType = {
    host: InventoryItem<any>;
    services?: InventoryItem<any>[]
    setServices?: React.Dispatch<React.SetStateAction<InventoryItem<any>[]>>
    fetchServices: () => Promise<void>
}

const HostContext = React.createContext<HostContextType | null>(null);

export function HostProvider({ children, host }: { children: React.ReactNode, host: InventoryItem<any> }) {
    const { api } = useApi()
    const [services, setServices] = React.useState<any[]>([])

    const fetchServices = async () => {
        api.get(`/api/infrastructure/host/${host.item_key}/services/`)
            .then((response: any) => setServices(response))
            .catch((error: any) => toast.error(error.message));
    }

    React.useEffect(() => {
        // do nothing for now
    }, [])

    return (
        <HostContext value={{host, services, setServices, fetchServices}}>
            {children}
        </HostContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useHost = () => {
    const reposContext = React.useContext(HostContext);

    if (!reposContext) {
        throw new Error("useHost has to be used within <HostContext>");
    }

    return reposContext;
};
