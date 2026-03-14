import React from "react";
import { InventoryItem } from "@/features/inventory/inventory.types.ts";
import AppIcon from "@/components/app-icon.tsx";

interface InventoryWidgetComponentProps {
    item: InventoryItem<any>;
    widgetType: string;
}

const FallbackWidget = ({ widgetType }: InventoryWidgetComponentProps) => {
    return <div key={widgetType} className={"text-red-500"}>{widgetType} widget not found</div>;
};

const JsonDataWidget = (props: InventoryWidgetComponentProps) => {
    const { item } = props;
    return (
        <div>
            <div className={"text-xs"}>
                [JSONHero] [ReactJSON] [Editor] [Raw] [Download]
            </div>
            <div>
                <pre className={"text-xs"}>{JSON.stringify(item, null, 2)}</pre>
            </div>
        </div>
    );
};
const PromptWidget = () => {
    //const { item } = props;
    return (
        <div>
            <div className={"text-xs"}>
                [Prompt Input] [Submit]
            </div>
            <div>
                <pre className={"text-xs"}>Prompt widget not implemented yet.</pre>
            </div>
        </div>
    );
};
const IrepositoryWidget = (props: InventoryWidgetComponentProps) => {
    const { item } = props;
    return (
        <div>
            <div className={"text-xs"}>
                [IRepository Specific Widget]
            </div>
            <div>
                {item?.github && "#github"}
            </div>
        </div>
    );
};
const InternetDomainWidget = (props: InventoryWidgetComponentProps) => {
    const { item } = props;
    const [showIframe, setShowIframe] = React.useState(false);

    const url = item?.id ? `https://${item.id}`:null;
    if (!url) {
        return <div>No domain name available</div>;
    }

    return (
        <div>
            <div>
                URL: <a href={url} target={`_blank`} rel="noopener noreferrer">{url}</a>
            </div>
            {showIframe ? <div>
                <iframe src={url} title={item.id} className={"w-full min-h-[400px]"}></iframe>
            </div>:<button className={"text-xs underline"} onClick={() => setShowIframe(true)}>Show Iframe</button>}
        </div>
    );
};

const GhRepositoryWidget = (props: InventoryWidgetComponentProps) => {
    const { item } = props;
    const ghData = item?.github || {};
    if (!ghData || Object.keys(ghData).length===0) {
        return <div>No GitHub data available</div>;
    }
    return (
        <div className={"flex flex-row space-x-1"}>
            <div className={"text-xs font-bold"}>
                [github]
            </div>
            <div className={"flex flex-row"}>{ghData?.private ? <span>Private</span>:<span>Public</span>}</div>
            <div className={"flex flex-row"}><AppIcon icon={"star"} size={16} /> Stars: {ghData?.stargazers_count} |</div>
            <div className={"flex flex-row"}><AppIcon icon={"fork"} size={16} /> Forks: {ghData?.forks_count} |</div>
            <div className={"flex flex-row"}><AppIcon icon={"issues"} size={16} /> Open Issues: {ghData?.open_issues_count}</div>
            <div>
                | {ghData?.html_url &&
                <a className={"text-secondary-foreground hover:underline"} href={ghData.html_url} target={`_blank`}
                   rel="noopener noreferrer">Open</a>}
            </div>
        </div>
    );
};

const widgetMap: Record<string, React.FC<InventoryWidgetComponentProps>> = {
    json: JsonDataWidget,
    prompt: PromptWidget,

    // inventory specific widgets
    irepository: IrepositoryWidget,
    iinternetdomain: InternetDomainWidget,

    // vendor
    "github-repository": GhRepositoryWidget,
};
export const getWidgetComponent = (widgetType: string): React.FC<InventoryWidgetComponentProps> => {
    return widgetMap[widgetType] || FallbackWidget;
};
