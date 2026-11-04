import { useLoaderData, useParams } from "react-router";
import { IconTool } from "@tabler/icons-react";
import { ToolsProvider, useTools } from "@/app/manage/tools/components/tools-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import { DetailEmpty, ListDetailLayout } from "@/components/layout/list-detail-layout.tsx";
import ToolList from "@/app/manage/tools/components/tool-list.tsx";
import { ToolDetails } from "@/app/manage/tools/components/tool-details.tsx";
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
    const { hostId } = useParams<{ hostId: string }>();
    const data = useLoaderData() as Tool[];

    if (!FEAT_TOOLS_ENABLED) {
        return <div className={"p-4"}>Tools feature is disabled.</div>;
    }
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return <MainContent>
        <Header title={"Tools"} subtitle={`Tools available on ${hostId}. Manage in mc.conf.json`} />
        <ToolsProvider tools={data || []} hostId={hostId}>
            <ToolsLayout />
        </ToolsProvider>
    </MainContent>;
};

export default ToolsPage;
