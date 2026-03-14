import React from "react";
import Form from "@rjsf/shadcn";
import validator from "@rjsf/validator-ajv8";
import { Button } from "@/components/ui/button.tsx";
import { InventoryActionDef, InventoryItem } from "@/features/inventory/inventory.types.ts";
import { useApi } from "@/context/api-context.tsx";
import { toast } from "react-toastify";
import { TaskProvider } from "@/app/tasks/components/task-provider.tsx";
import TaskProgress from "@/app/tasks/components/task-progress.tsx";
import TaskLog from "@/app/tasks/components/task-log.tsx";
import { useInventory } from "@/app/inventory/components/inventory-provider.tsx";
import { UiSchema } from "@rjsf/utils";

const InventoryActionForm = ({def, item}: {def: InventoryActionDef, item: InventoryItem<any>}) => {
    const { itemType, metadata } = useInventory();
    const { api } = useApi()
    // if (!currentItem) {
    //     return <div>No item selected</div>;
    // }
    //const item = currentItem;

    const [response, setResponse] = React.useState<any>(null);
    const [taskId, setTaskId] = React.useState<string | null>(null);

    const handleFormSubmit = async ({formData}: any) => {
        console.log("Action Form submitted:", formData);
        const timeout = def?.timeout || 30000;
        try {
            const p = api.post(`/api/inventory/${itemType}/${item.id}/action/${def.id}`, formData, { timeout: 60000 })
                .then((res: any) => {
                    setResponse(res);
                    return res;
                })
                // .catch((err: any) => {
                //     console.error("Error executing action:", err);
                //     //toast.error(`Error executing action "${def.id}"": ${err.message || err}`);
                //     throw err;
                // })

            const response: any = await toast.promise(p, {
                pending: `Executing action "${def.id}""...`,
                success: `Action "${def.id}" executed"`,
                error: `Error executing action "${def.id}""`,
            })
            console.log("Action executed successfully:", response);

            // check if response contains an "error" field
            if (response && response.error) {
                toast.error(`Error executing action "${def.id}"": ${response.error}`);
                return;
            }

            // check if response contains a task_id -> track the task
            if (response && response.task_id) {
                const taskId = response.task_id;
                // open the task drawer
                //openTaskDrawer(taskId);
                setTaskId(taskId);
                toast.info(`Action "${def.id}" is being processed as task ${taskId}`);
            }

            //toast.success(`Action "${def.id}" executed"`);
        } catch (error: any) {
            console.error("Error executing action:", error);
            toast.error(`Error": ${error?.response?.data?.error || error?.message || "Unknown error"}`);
        }
    }

    const handleFormChange = ({formData}: any) => {
        console.log("Action Form changed:", formData);
    }

    return (
        <div>
            <div className={"py-4"}>
                <h1>{def.name} - {item.id}</h1>
            </div>

            <Form
                schema={def?.inputSchema || {}}
                uiSchema={def?.uiSchema as UiSchema || {}}
                onSubmit={handleFormSubmit}
                onChange={handleFormChange}
                validator={validator}
            >
                <div className="mt-4 w-max">
                    <Button type="submit" className={"w-max"}>Submit</Button>
                </div>
            </Form>
            {taskId && (
                <div className={"mt-8"}>
                    <h2>Task started: {taskId}</h2>
                    <TaskProvider taskId={taskId} onComplete={(result) => {
                        console.log("Task completed with result:", result);
                        toast.success(`Task ${taskId} completed`);
                    }}>
                        <TaskProgress />
                        <TaskLog />

                    </TaskProvider>
                </div>)}
            {response && <div className={"mt-2"}>
                <h2>Response:</h2>
                <pre className={"text-xs overflow-auto border font-mono whitespace-pre-wrap break-words"}>{JSON.stringify(response, null, 2)}</pre>
            </div>}
        </div>
    );
};

export default InventoryActionForm;
