import { useTask } from "@/app/tasks/components/task-provider.tsx";

const TaskLog = () => {
    const { logRef } = useTask()

    return (
        <div ref={logRef} id="tasks-log" className="overflow-auto overflow-y-scroll border p-2 font-mono text-sm h-[200px] break-words whitespace-pre-wrap bg-black text-green-500">
            <p>Task log will appear here...</p>
        </div>
    );
};

export default TaskLog;
