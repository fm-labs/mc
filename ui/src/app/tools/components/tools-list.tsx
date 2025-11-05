import { Button } from "@/components/ui/button.tsx";
import { useTools } from "@/app/tools/components/tools-provider.tsx";

const ToolsList = ({tools}: {tools: Tool[]}) => {
    const { setCurrentTool } = useTools();

    return (
        <div>
            {tools && tools.length > 0 && tools.map((tool: Tool) => {
                return <div key={tool.name} style={{ marginBottom: "20px" }}>
                    <h3>{tool.name}</h3>
                    {/*<pre>{JSON.stringify(tool.def[tool.name])}</pre>*/}
                    {tool.commands && Object.entries(tool.commands)
                        .filter(([key, _value]) => key!=="_docker")
                        .map(([key, value]: [string, any]) => {
                            return <div key={key}>
                                {key} ({value?.description})
                                <Button onClick={() => setCurrentTool(tool, key)}>{key}</Button>
                            </div>;
                        })}
                </div>;

            })}
        </div>
    );
};

export default ToolsList;
