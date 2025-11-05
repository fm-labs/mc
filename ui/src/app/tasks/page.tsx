import { Button } from "@/components/ui/button.tsx";
import {  FEAT_TASKS_ENABLED } from "@/constants.ts";
import React from "react";
import { useApi } from "@/context/api-context.tsx";
import { EventSourceReader } from "@/components/event-source-reader.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import { TasksProvider } from "@/app/tasks/components/tasks-context.tsx";
import { TaskProvider } from "@/app/tasks/components/task-provider.tsx";
import TaskProgress from "@/app/tasks/components/task-progress.tsx";
import TaskLog from "@/app/tasks/components/task-log.tsx";


const TasksPage = () => {
    if (!FEAT_TASKS_ENABLED) {
        return <div className={"p-4"}>Tasks feature is disabled.</div>
    }

    const { api, apiBaseUrl } = useApi();
    const [streamingCommand, setStreamingCommand] = React.useState<string | null>(null);
    const [taskId, setTaskId] = React.useState<string | null>(null);

    // const logRef = React.useRef<HTMLDivElement | null>(null);
    // const clearLog = () => {
    //     if (logRef.current) {
    //         logRef.current.innerHTML = "";
    //     }
    // };
    //
    // const appendLog = (message: string) => {
    //     if (logRef.current) {
    //         const newLogEntry = document.createElement("div");
    //         newLogEntry.textContent = message;
    //         logRef.current.appendChild(newLogEntry);
    //         logRef.current.scrollTop = logRef.current.scrollHeight;
    //     }
    // };

    const handleSubmitToolAction = (_options?: any) => async () => {
        try {
            const response = await api.submitToolAction("ping", "_", { host: "localhost" });
            console.log("Tool action submitted successfully:", response);
        } catch (error) {
            console.error("Error submitting tool action:", error);
        }
    };

    const handleSubmitTaskAction = (_options?: any) => async () => {
        try {
            const response = await api.submitCeleryTask({
                task_name: "mc.plugin.demo.tasks.task_long_running_with_progress",
                parameters: { "duration": 10 },
            });
            console.log("Task action submitted successfully:", response);
            const taskId = response.task_id;
            setTaskId(taskId);
        } catch (error) {
            console.error("Error submitting task action:", error);
        }
    };

    return (
        <MainContent>
            <div className={"mb-8"}>
                <h1>SSE</h1>
                <div>
                    <Button onClick={() => setStreamingCommand(null)}>Stop streaming</Button>{" | "}
                    <Button onClick={() => setStreamingCommand("tick")}>SSE tick</Button>
                    <Button onClick={() => setStreamingCommand("ping")}>SSE subprocess</Button>{" | "}
                </div>
                <hr />
                {streamingCommand &&
                    <EventSourceReader url={`${apiBaseUrl}sse/stream/${streamingCommand}`} />}
            </div>

            <TasksProvider>
                <h1>Tasks</h1>
                <div>
                    <Button onClick={handleSubmitTaskAction({})}>Celery Task</Button>{" | "}
                    <Button onClick={handleSubmitToolAction({})}>Run Ping Tool in foreground</Button>
                    <Button onClick={handleSubmitToolAction({ stream: true })}>Stream Ping Tool in foreground</Button>
                    <Button onClick={handleSubmitToolAction({ background: true })}>Run Ping Tool in background</Button>
                </div>
                <hr />
                {taskId && <TaskProvider taskId={taskId}>
                    <TaskProgress />
                    <TaskLog />
                </TaskProvider>}

            </TasksProvider>
        </MainContent>
    );
};

export default TasksPage;
