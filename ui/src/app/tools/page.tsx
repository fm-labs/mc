import { useLoaderData } from "react-router";
import { ToolsProvider } from "@/app/tools/components/tools-provider.tsx";
import { ToolsDialogs } from "@/app/tools/components/tool-dialogs.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import ToolsGrid from "@/app/tools/components/tools-grid.tsx";
import { FEAT_TOOLS_ENABLED } from "@/constants.ts";

const ToolsPage = () => {
    if (!FEAT_TOOLS_ENABLED) {
        return <div className={"p-4"}>Tools feature is disabled.</div>
    }

    const data = useLoaderData();

    return (
        <MainContent>
            <ToolsProvider tools={data}>
                <ToolsGrid tools={data} />
                {/*<ToolsList tools={data} />*/}
                <ToolsDialogs />
            </ToolsProvider>
        </MainContent>
    );
};

export default ToolsPage;
