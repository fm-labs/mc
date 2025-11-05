import React, { PropsWithChildren } from "react";
import { Button } from "@/components/ui/button.tsx";
import { TaskStatusResponse, TaskSubmissionResponse } from "@/features/tasks/tasks.types.ts";
import { useApi } from "@/context/api-context.tsx";

interface TaskButtonProps extends PropsWithChildren<any> {
    label: string;
    promise: () => Promise<any>;
    onSuccess?: (result: any) => void;
    onFailure?: (error: Error) => void;
}

const TaskButton = ({ promise, onSuccess, onFailure, label }: TaskButtonProps) => {
    const { api } = useApi()
    const [loading, setLoading] = React.useState(false);
    const [monitoring, setMonitoring] = React.useState(false);
    const [result, setResult] = React.useState<any | null>(null);
    const [taskId, setTaskId] = React.useState<string | null>(null);

    const handleClick = () => {
        submitTask();
    };

    const submitTask = React.useCallback(() => {
        setLoading(true);
        setResult(null);
        setTaskId(null);
        setMonitoring(false);

        promise()
            .then((result: TaskSubmissionResponse) => {
                console.log("Task submitted", result);
                const taskId = result?.task_id;
                if (!taskId) {
                    throw new Error("Task ID not found");
                }
                setTaskId(taskId);
                setMonitoring(true);
                //addTask(result)
                //console.log('Task ID', taskId)
                return result;
            })
            .catch((error) => {
                if (onFailure) {
                    onFailure(error);
                }
                setResult(error);
                setLoading(false);
                console.error("Task submission error", error);
            })
            .finally(() => {
            });
    }, [promise, onFailure, setLoading, setResult, setTaskId, setMonitoring]);

    const fetchTaskStatus = React.useCallback(() => {
        if (!taskId) {
            return;
        }
        console.log("Fetching task status", taskId);
        api.getCeleryTaskStatus()(taskId)
            .then((statusData: TaskStatusResponse) => {
                console.log("Task status", taskId, statusData);
                setResult(statusData);
                setLoading(false);

                //updateTask(taskId, statusData)
                if (statusData.state?.toLowerCase()==="success") {
                    console.log("Task success", taskId);
                    setMonitoring(false);
                    if (onSuccess) {
                        onSuccess(statusData?.result);
                    }
                } else if (statusData.state?.toLowerCase()==="failure") {
                    console.error("Task failed", taskId);
                    setMonitoring(false);
                    if (onFailure) {
                        onFailure(statusData?.error ? new Error(statusData.error) : new Error("Task failed"));
                    }
                }
            })
            .catch((error: any) => {
                console.error("Task status error", taskId, error);
                setLoading(false);
                setResult(undefined);
                if (onFailure) {
                    onFailure(error);
                }
                setResult(error);
            });
    }, [taskId, setResult, setLoading, onSuccess, onFailure, setMonitoring]);

    React.useEffect(() => {
        if (!taskId || !monitoring) {
            return;
        }

        console.log("Monitoring task", taskId);
        const timer = setInterval(fetchTaskStatus, 2500);

        return () => {
            console.log("Cleaning up task monitor", taskId);
            clearInterval(timer);
        };
    }, [taskId, monitoring]);


    return (
        <Button variant={"secondary"} onClick={handleClick} title={result}>
            {!loading ? (
                label
            ):(
                <>
                    Loading...
                </>
            )}
        </Button>
    );
};

export default TaskButton;
