import { Button } from "@/components/ui/button.tsx";
import { useTools } from "@/app/tools/components/tools-provider.tsx";
import { Separator } from "@/components/ui/separator.tsx";
import { IconWreckingBall } from "@tabler/icons-react";

const ToolsGrid = ({tools}: {tools: Tool[]}) => {
    const { setCurrentTool } = useTools();

    return (
        <div>
            <Separator className="shadow-sm" />
            <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 md:grid-cols-2 lg:grid-cols-3">
                {tools && tools.length > 0 && tools.map((tool) => (
                    <li
                        key={tool.name}
                        className="rounded-lg border p-4 hover:shadow-md"
                    >
                        <div className="mb-8 flex items-center justify-between">
                            <div
                                className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
                            >
                                <IconWreckingBall />
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentTool(tool, null)}
                                //className={`${tool.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                            >
                                Open
                            </Button>
                        </div>
                        <div>
                            <h2 className="mb-1 font-semibold">{tool.name}</h2>
                            <p className="line-clamp-2 text-gray-500">{tool?.description || "No description"}</p>
                            <p>{`${tool.commands ? Object.keys(tool.commands).length : 'No'} commands available`}</p>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ToolsGrid;
