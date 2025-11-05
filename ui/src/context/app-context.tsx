import React from "react";

type AppContextType = {
    config: any,
}

export const AppContext = React.createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode, config: any }> = ({ children, config }) => {

    return (
        <AppContext.Provider value={{ config }}>
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
