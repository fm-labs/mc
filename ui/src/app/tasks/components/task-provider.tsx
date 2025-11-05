import React from "react";
import { useApi } from "@/context/api-context.tsx";

type TaskContextType = {
    taskId: string | null;
    state: string;
    progress?: number /* | { current: number, total: number, status?: string }*/;
    result?: any;
    logRef: React.RefObject<HTMLDivElement | null>;
    clearLog: () => void;
}

const TaskContext = React.createContext<TaskContextType | null>(null);

interface TaskProviderProps {
    children: React.ReactNode;
    taskId: string;
    onComplete?: (taskId: string, result: any) => void;
    onError?: (taskId: string, error: Error) => void;
    onStatusChange?: (taskId: string, state: string) => void;
}

export function TaskProvider({ children, taskId }: TaskProviderProps) {
    const { api } = useApi();

    const logRef = React.useRef<HTMLDivElement>(null);
    const [progress, setProgress] = React.useState<number>(0);
    const [result, setResult] = React.useState<any>(null);
    const [state, setState] = React.useState<string>("UNKNOWN");

    const clearLog = () => {
        if (logRef.current) {
            logRef.current.innerHTML = "";
        }
    };

    const appendLog = (message: string) => {
        if (logRef.current) {
            const newLogEntry = document.createElement("div");
            newLogEntry.textContent = message;
            logRef.current.appendChild(newLogEntry);
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    };

    React.useEffect(() => {
        if (!taskId) {
            return;
        }

        clearLog();
        setProgress(0);
        appendLog(`Task submitted with ID: ${taskId}`);

        // Polling for task status every 2 seconds
        const intervalId = setInterval(async () => {
            try {
                const statusResponse = await api.getCeleryTaskStatus(taskId);
                setResult(statusResponse?.result);
                setState(statusResponse?.state);

                console.log("Task status:", statusResponse);
                if (statusResponse.state==="SUCCESS" || statusResponse.state==="FAILURE") {
                    clearInterval(intervalId);
                    console.log("Task completed with state:", statusResponse.state);
                    setProgress(100);
                    appendLog(`Task completed with state: ${statusResponse.state}`);

                    const result = statusResponse.result;
                    if (statusResponse.state==="SUCCESS") {
                        appendLog(`Result: ${JSON.stringify(result)}`);
                    } else {
                        appendLog(`Error: ${statusResponse?.error || JSON.stringify(result)}`);
                    }
                } else if (statusResponse.state==="PROGRESS") {
                    const progressDetail = statusResponse.progress;
                    setProgress((progressDetail?.current / progressDetail?.total) || 0);
                    appendLog(`Progress: ${progressDetail?.current}/${progressDetail?.total} - ${progressDetail.status}`);
                }
            } catch (statusError) {
                console.error("Error fetching task status:", statusError);
                clearInterval(intervalId);
            }
        }, 1000);

        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        }

    }, [taskId]);

    return (
        <TaskContext.Provider value={{ taskId, progress, result, state, logRef, clearLog }}>
            {children}
        </TaskContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTask = () => {
    const taskContext = React.useContext(TaskContext);

    if (!taskContext) {
        throw new Error("useTask has to be used within <TaskProvider>");
    }

    return taskContext;
};
