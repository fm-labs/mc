import * as React from "react";
import { IconTerminal2, IconWorld } from "@tabler/icons-react";
import { SearchableList } from "@/components/layout/list-detail-layout.tsx";
import { useTools } from "@/app/tools/components/tools-provider.tsx";
import { getToolType } from "@/app/tools/components/tool-utils.ts";

const ToolList = () => {
    const { tools, currentTool, setCurrentTool } = useTools();

    const items = React.useMemo(() => tools.map((tool) => ({
        id: tool.name,
        title: tool.name,
        subtitle: tool.description,
        icon: getToolType(tool) === "http" ? <IconWorld size={16} /> : <IconTerminal2 size={16} />,
    })), [tools]);

    return (
        <SearchableList
            items={items}
            selectedId={currentTool?.name}
            onSelect={(name) => setCurrentTool(tools.find((t) => t.name === name) || null)}
            noun="tools"
        />
    );
};

export default ToolList;
