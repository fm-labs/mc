import React from "react";
import {Helmet} from "react-helmet-async";

type AppContextType = {
    config: any,
}

export const AppContext = React.createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode, config: any }> = ({ children, config }) => {

    const pageTitleStr = React.useMemo(() => {
        const s = String(window.location.hostname)
        console.log("HOST", s)
        return `mc | ${s}`
    }, [])

    return (
        <AppContext.Provider value={{ config }}>
            <Helmet>
                <title>{pageTitleStr}</title>
            </Helmet>
            {children}
        </AppContext.Provider>
    );
}

export const useAppContext = () => {
    const context = React.useContext(AppContext);
    if (!context) {
        throw new Error("useAppContext must be used within an AppProvider");
    }
    return context;
}
