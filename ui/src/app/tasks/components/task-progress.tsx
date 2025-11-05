import { Progress } from "@/components/ui/progress.tsx";
import { useTask } from "@/app/tasks/components/task-provider.tsx";

const TaskProgress = () => {
    const { progress } = useTask()
    
    return (
        <div className="w-full rounded-full h-4 mb-4 p-4">
            {/*<div
                        className="bg-blue-600 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    >{`${progress}%`}</div>*/}
            <Progress value={progress} />
        </div>
    );
};

export default TaskProgress;
