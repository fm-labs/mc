import React from "react";

type TasksContextType = {
    config?: any,
    activeTasks: Record<string, any>,
    addTask: (taskId: string, taskData: any) => void,
    removeTask: (taskId: string) => void,
}

export const TasksContext = React.createContext<TasksContextType | undefined>(undefined);

export const TasksProvider: React.FC<{ children: React.ReactNode, config?: any }> = ({ children, config }) => {
    // @ts-ignore
    const [tasks, setTasks] = React.useState<Record<string, any>>({});

    const addTask = (taskId: string, taskData: any) => {
        setTasks((prevTasks) => ({
            ...prevTasks,
            [taskId]: taskData,
        }));
    }

    const removeTask = (taskId: string) => {
        setTasks((prevTasks) => {
            const newTasks = { ...prevTasks };
            delete newTasks[taskId];
            return newTasks;
        });
    }

    return (
        <TasksContext.Provider value={{ config, activeTasks: tasks, addTask, removeTask }}>
            {children}
        </TasksContext.Provider>
    );
}


export const useTasks = () => {
    const context = React.useContext(TasksContext);

    if (!context) {
        throw new Error("useTasks has to be used within <TasksContext>");
    }

    return context;
}
