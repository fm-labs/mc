import React from "react";

type MasterContextType = {
    lastNotification: string | null;
    addNotification: (message: string) => void;
}

export const MasterContext = React.createContext<MasterContextType | null>(null);

const texts = [
    "Welcome to the Ultimate AI-Powered DevOps & Cloud Management Tool!",
    "Streamline your workflows with cutting-edge AI technology.",
    "Automate your cloud infrastructure like never before.",
    "Try our new AI-driven deployment features!",
    "Just enter commands in the input box <----- to get started.",
    "Need help? Type 'help' in the input box for assistance.",
];


export const MasterContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [notifications, setNotifications] = React.useState<string[]>(texts);
    const [lastNotification, setLastNotification] = React.useState<string | null>(null);

    const addNotification = (message: string) => {
        setNotifications(prev => [...prev, message]);
    }

    const removeNotification = (index: number) => {
        setNotifications(prev => prev.filter((_, i) => i !== index));
    }

    const contextValue: MasterContextType = {
        addNotification,
        lastNotification
    };

    React.useEffect(() => {
        if (notifications.length > 0 && !lastNotification) {
            const nextNotification = notifications[0];
            setLastNotification(nextNotification);
        }
    }, [notifications, lastNotification]);

    React.useEffect(() => {
        if (lastNotification) {
            console.info("New Notification:", lastNotification);
            //toast.info(lastNotification);
            const timer = setTimeout(() => {
                removeNotification(0);
                setLastNotification(null);
            }, 5000);

            return () => clearTimeout(timer);
        }
    }, [lastNotification]);

    return (
        <MasterContext.Provider value={contextValue}>
            {children}
        </MasterContext.Provider>
    );
}

export const useMasterContext = () => {
    const context = React.useContext(MasterContext);
    if (!context) {
        throw new Error("useMasterContext must be used within a MasterContextProvider");
    }
    return context;
}
