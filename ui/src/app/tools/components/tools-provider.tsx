import React from "react";
import { useSelectedSearchParam } from "@/hooks/use-selected-search-param.ts";

type ToolsContextType = {
    tools: Tool[]
    currentTool: Tool | null
    setCurrentTool: (tool: Tool | null) => void
}

const ToolsContext = React.createContext<ToolsContextType | null>(null);

// The selected tool lives in the URL (?tool=name) so it survives reloads and can be linked to.
export function ToolsProvider({ children, tools }: { children: React.ReactNode, tools: Tool[] }) {
    const [selectedName, setSelectedName] = useSelectedSearchParam("tool");

    const currentTool = React.useMemo(
        () => tools.find((t) => t.name === selectedName) || null,
        [tools, selectedName],
    );

    const setCurrentTool = React.useCallback(
        (tool: Tool | null) => setSelectedName(tool?.name ?? null),
        [setSelectedName],
    );

    return (
        <ToolsContext value={{ currentTool, setCurrentTool, tools }}>
            {children}
        </ToolsContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTools = () => {
    const toolsContext = React.useContext(ToolsContext);

    if (!toolsContext) {
        throw new Error("useTools has to be used within <ToolsContext>");
    }

    return toolsContext;
};
