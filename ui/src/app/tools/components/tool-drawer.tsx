import * as React from "react";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";

import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetClose,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "react-toastify";
import { useApi } from "@/context/api-context.tsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.tsx";

type ToolDrawerProps = {
    open: boolean
    onOpenChange: (open: boolean) => void
    tool: Tool,
    commandName: string | null
}

export function ToolDrawer({
                               open,
                               onOpenChange,
                               tool,
                               commandName: _commandName,
                           }: ToolDrawerProps) {

    const { api } = useApi();

    const toolName = tool.id;

    const [commandName, setCommandName] = React.useState<string | null>(_commandName);
    const [formData, setFormData] = React.useState<any>({});
    const [response, setResponse] = React.useState<any>(null);

    const commandDef = React.useMemo(() => {
        if (!commandName) return null;
        if (!tool.commands[commandName]) {
            console.error("Command not found in tool:", commandName, tool);
            return null;
        }
        return tool.commands[commandName];
    }, [commandName, tool]);

    const inputSchema = React.useMemo(() => {
        return commandDef?.input_schema || {
            type: "object",
            properties: {},
        };
    }, [commandDef?.input_schema]);

    // const uiSchema = React.useMemo(() => {
    //     return commandDef?.ui_schema || {};
    // }, [commandDef?.ui_schema]);

    const onFormChange = (data: any) => {
        // handle form submission
        console.log("Form changed:", data.formData);
        //onOpenChange(false);
        setFormData(data.formData);
    }


    const onFormSubmit = async (data: any) => {
        // handle form submission
        console.log("Form submitted:", data.formData);

        if (!commandName) {
            console.error("No command name selected");
            return;
        }

        const p = api.submitToolAction(toolName, commandName, data.formData).then((response: any) => {
            console.log("Tool action response", response);
            //toast.success("Tool action submitted");
            setResponse(response);
            //onOpenChange(false);
            return response;
        })
        await toast.promise(p, {
            pending: 'Submitting tool action...',
            success: 'Tool action submitted',
            error: 'Error submitting tool action'
        });
    };

    const handleSubmitBackgroundClick = async () => {
        // handle form submission
        console.log("Form submitted for background task:", formData);

        if (!commandName) {
            console.error("No command name selected");
            return;
        }

        const p = api.submitToolActionBackground(toolName, commandName, formData).then((response: any) => {
            console.log("Tool action background task response", response);
            //toast.success("Tool action background task submitted");
            setResponse(response);
            //onOpenChange(false);
            return response;
        })
        await toast.promise(p, {
            pending: 'Submitting tool action as background task...',
            success: 'Tool action background task submitted',
            error: 'Error submitting tool action background task'
        });
    }

    return (
        <Sheet
            open={open}
            onOpenChange={(v) => {
                onOpenChange(v);
            }}
        >
            <SheetContent className="flex flex-col overflow-y-scroll">
                <SheetHeader className="text-start">
                    <SheetTitle>{toolName}</SheetTitle>
                    <SheetDescription>
                        {tool?.description}
                    </SheetDescription>
                    <hr />
                    <div>
                        <Select value={commandName || ""} onValueChange={(value) => {
                            console.log("Selected command:", value);
                            setResponse(null);
                            setCommandName(value);
                        }}>
                            <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select Command" />
                            </SelectTrigger>
                            <SelectContent>
                                {Object.keys(tool.commands).map((cmdName) => (
                                    <SelectItem
                                        key={cmdName}
                                        value={cmdName}
                                    >
                                        {cmdName}
                                    </SelectItem>
                                ))}
                            </SelectContent>

                        </Select>
                    </div>
                    <hr />
                    {commandDef && <div>
                        {commandDef?.description}
                        <hr />
                        <pre className={"bg-gray-900 mt-2 p-2 text-sm text-wrap"}>{(commandDef.cmd as string[]).join(" ")}</pre>
                    </div>}
                </SheetHeader>
                <div className={"px-4"}>
                    {commandDef && inputSchema && <Form
                        id={"tool-command-form"}
                        schema={inputSchema}
                        //uiSchema={uiSchema}
                        //formData={toolDef}
                        onSubmit={onFormSubmit}
                        onChange={onFormChange}
                        validator={validator}
                    >
                        {' '}
                    </Form>}
                </div>
                {response && <div className="flex-1">
                    Response:
                    <pre className="max-h-48 overflow-auto bg-gray-100 p-2 text-sm">{JSON.stringify(response, null, 2)}</pre>
                </div>}
                <SheetFooter className="gap-2">
                    {commandDef && <Button form={"tool-command-form"} type="submit">Run Command</Button>}
                    {commandDef && <Button
                        form={"tool-command-form"}
                        onClick={handleSubmitBackgroundClick}
                        type="submit">Run Command in Background</Button>}
                    <SheetClose asChild>
                        <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
                    </SheetClose>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
