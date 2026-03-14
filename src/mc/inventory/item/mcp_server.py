from mc.util.mcp_client import build_stdio_client, build_streamable_http_client, list_mcp_tools


def handle_mcp_server_connect(item: dict, action_params: dict) -> dict:
    props = item
    return {"status": "OK", "output": {}}


def build_mcp_client_from_item(item: dict):
    props = item
    server_type = props.get("type").lower()
    if server_type == "stdio":
        command = props.get("command", "").strip()
        if not command:
            raise ValueError("MCP server 'command' property is required for stdio type.")

        args_str = props.get("args", "")  # space-separated string as put in shell
        args_list = args_str.split(" ") if args_str else []
        env_str = props.get("env", "")  # comma-separated key=value pairs
        env_dict = {}
        if env_str:
            for pair in env_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    env_dict[key.strip()] = value.strip()

        mcpclient = build_stdio_client(command=command, args=args_list, env=env_dict)
    elif server_type == "streamable-http":
        server_url = props.get("url")
        token = props.get("token")
        mcpclient = build_streamable_http_client(server_url, token)
    else:
        raise ValueError(f"Unsupported MCP server type: {server_type}")
    return mcpclient

async def handle_mcp_server_list_actions(item: dict, action_params: dict) -> dict:
    mcpclient = build_mcp_client_from_item(item)
    tools = await list_mcp_tools(mcpclient)
    return {"status": "OK", "output": {"tools": tools}}

async def handle_mcp_server_call_action(item: dict, action_params: dict) -> dict:
    mcpclient = build_mcp_client_from_item(item)

    tool_name = action_params.get("tool_name")
    if not tool_name:
        raise ValueError("Parameter 'tool_name' is required.")
    tool_args = action_params.get("tool_args", {})

    res = await mcpclient.call_tool(tool_name, tool_args)
    #res = await mcpclient.call_tool_mcp(tool_name, tool_args)
    return {"status": "OK", "output": {"result": res}}

actions = {
    "connect": handle_mcp_server_connect,
    "list_actions": handle_mcp_server_list_actions,
}