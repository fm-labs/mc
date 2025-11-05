import React from "react";
import { useApi } from "@/context/api-context.tsx";

type KitchensinkContextType = {
    fetchInventoryItems: (itemType: string) => Promise<void>;

    dialogElement: React.ReactNode | null;
    setDialogElement: React.Dispatch<React.SetStateAction<React.ReactNode | null>>;
}

const KitchensinkContext = React.createContext<KitchensinkContextType | null>(null);

export function KitchensinkProvider({ children }: { children: React.ReactNode }) {
    const { api } = useApi();
    const [dialogElement, setDialogElement] = React.useState<React.ReactNode | null>(null);

    const fetchInventoryItems = React.useCallback(async (itemType: string) => {
        try {
            const response = await api.get("/api/inventory/" + itemType);
            console.log("Data fetched:", response);
            return response;
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [api]);

    return (
        <KitchensinkContext value={{fetchInventoryItems, dialogElement, setDialogElement}}>
            {children}
        </KitchensinkContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useKitchensink = () => {
    const reposContext = React.useContext(KitchensinkContext);

    if (!reposContext) {
        throw new Error("useKitchensink has to be used within <KitchensinkContext>");
    }

    return reposContext;
};
