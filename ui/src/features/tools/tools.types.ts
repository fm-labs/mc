
type Tool = ToolDefinition

type ToolDefinition = {
    id: string,
    name: string,
    description?: string;
    commands: {
        [commandName: string]: ToolCommandDefinition
    }
}

type ToolCommandDefinition = {
    description?: string;
    cmd: string | string[];
    input_schema?: any;
    output_schema?: any;
}
