import React, { useState } from "react";
import useDialogState from "@/hooks/use-dialog-state";

type ToolsDialogType = "run"

type ToolsContextType = {
    open: ToolsDialogType | null
    setOpen: (str: ToolsDialogType | null) => void
    tools: Tool[]
    currentTool: Tool | null
    //setCurrentTool: React.Dispatch<React.SetStateAction<Tool | null>>
    commandName: string | null
    //setCommandName: React.Dispatch<React.SetStateAction<string | null>>
    setCurrentTool: (tool: Tool | null, command: string | null) => void
}

const ToolsContext = React.createContext<ToolsContextType | null>(null);

export function ToolsProvider({ children, tools }: { children: React.ReactNode, tools: Tool[] }) {
    const [open, setOpen] = useDialogState<ToolsDialogType>(null);
    const [currentTool, _setCurrentTool] = useState<Tool | null>(null);
    const [commandName, _setCommandName] = useState<string | null>(null);

    const setCurrentTool = (tool: Tool | null, command: string | null): void => {
        _setCurrentTool(tool);
        _setCommandName(command);
        setOpen('run')
    }

    return (
        <ToolsContext value={{ open, setOpen, currentTool, setCurrentTool, commandName, tools }}>
            {children}
        </ToolsContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTools = () => {
    const reposContext = React.useContext(ToolsContext);

    if (!reposContext) {
        throw new Error("useTools has to be used within <ToolsContext>");
    }

    return reposContext;
};
