import { useLoaderData } from "react-router";
import { IconTool } from "@tabler/icons-react";
import { ToolsProvider, useTools } from "@/app/tools/components/tools-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import { DetailEmpty, ListDetailLayout } from "@/components/layout/list-detail-layout.tsx";
import ToolList from "@/app/tools/components/tool-list.tsx";
import { ToolDetails } from "@/app/tools/components/tool-details.tsx";
import { FEAT_TOOLS_ENABLED } from "@/constants.ts";
import Header from "@/components/header.tsx";

const ToolsLayout = () => {
    const { currentTool } = useTools();

    return (
        <ListDetailLayout list={<ToolList />}>
            {currentTool
                // key resets form/output state when switching tools
                ? <ToolDetails key={currentTool.name} tool={currentTool} />
                : <DetailEmpty icon={<IconTool size={32} stroke={1.5} />}>
                    Select a tool from the list to see its details and run it.
                </DetailEmpty>}
        </ListDetailLayout>
    );
};

const ToolsPage = () => {
    if (!FEAT_TOOLS_ENABLED) {
        return <div className={"p-4"}>Tools feature is disabled.</div>
    }

    const data = useLoaderData() as Tool[];

    return (
        <MainContent>
            <Header title={"Tools"} subtitle={"Available tools. Manage in mc.conf.json"} />
            <ToolsProvider tools={data || []}>
                <ToolsLayout />
            </ToolsProvider>
        </MainContent>
    );
};

export default ToolsPage;
