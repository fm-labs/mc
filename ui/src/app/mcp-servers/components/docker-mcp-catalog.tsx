import React from "react";
import { useDockerMcpCatalog } from "@/app/mcp-servers/components/docker-mcp-catalog-provider.tsx";
import { Button } from "@/components/ui/button";
import Form from "@rjsf/shadcn";
import validator from "@rjsf/validator-ajv8";
import ReactJson from "@microlink/react-json-view";
import { Separator } from "@/components/ui/separator.tsx";
import { useApi } from "@/context/api-context.tsx";
import {RJSFSchema} from "@rjsf/utils";

/**
 * Render the docker MCP toolkit catalog
 *
 * Example data:
 * "brave": {
 *       "description": "Search the Web for pages, images, news, videos, and more using the Brave Search API.",
 *       "title": "Brave Search",
 *       "type": "server",
 *       "dynamic": {},
 *       "dateAdded": "2025-05-05T20:08:35Z",
 *       "image": "mcp/brave-search@sha256:b903e1ad948114517fa7dc767a9bf4c2d1b9529164bcc0fb9c58b344c56aa335",
 *       "ref": "",
 *       "readme": "http://desktop.docker.com/mcp/catalog/v3/readme/brave.md",
 *       "toolsUrl": "http://desktop.docker.com/mcp/catalog/v3/tools/brave.json",
 *       "source": "https://github.com/brave/brave-search-mcp-server/tree/a25160bcad9cded587b8ed94eacf9688a1b552de",
 *       "upstream": "https://github.com/brave/brave-search-mcp-server",
 *       "remote": {},
 *       "icon": "https://avatars.githubusercontent.com/u/12301619?s=200\u0026v=4",
 *       "tools": [
 *         {
 *           "name": "brave_image_search",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         },
 *         {
 *           "name": "brave_local_search",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         },
 *         {
 *           "name": "brave_news_search",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         },
 *         {
 *           "name": "brave_summarizer",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         },
 *         {
 *           "name": "brave_video_search",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         },
 *         {
 *           "name": "brave_web_search",
 *           "parameters": {
 *             "type": "",
 *             "properties": null,
 *             "required": null
 *           },
 *           "container": {}
 *         }
 *       ],
 *       "secrets": [
 *         {
 *           "name": "brave.api_key",
 *           "env": "BRAVE_API_KEY",
 *           "example": "YOUR_API_KEY_HERE"
 *         }
 *       ],
 *       "env": [
 *         {
 *           "name": "BRAVE_MCP_TRANSPORT",
 *           "value": "stdio"
 *         }
 *       ],
 *       "prompts": 0,
 *       "resources": null,
 *       "metadata": {
 *         "pulls": 55668,
 *         "stars": 20,
 *         "githubStars": 311,
 *         "category": "search",
 *         "tags": [
 *           "brave",
 *           "search"
 *         ],
 *         "license": "MIT License",
 *         "owner": "brave"
 *       },
 *       "oauth": {}
 *     }
 *
 *
 * @constructor
 */
const DockerMcpCatalog = () => {
    const { api } = useApi()
    const { registry } = useDockerMcpCatalog()
    const [selectedServerKey, setSelectedServerKey] = React.useState<string | null>(null);
    const [selectedServer, setSelectedServer] = React.useState<any | null>(null);
    const [result, setResult] = React.useState<any | null>(null);

    const buildConnectJsonSchemaForServer = (serverDef: any): RJSFSchema => {

        const properties: any = {}

        // env vars
        // const envs = serverDef?.env || []
        // envs.forEach((envVar: any) => {
        //     properties[envVar.name] = {
        //         type: "string",
        //         title: envVar.name,
        //         default: envVar.value || ""
        //     }
        // })
        console.log("serverDevf:", serverDef)
        console.log("serverDef config:", serverDef?.config)
        const config = serverDef?.config && Array.isArray(serverDef?.config)
            ? serverDef?.config[0] || {} : {}

        // add secrets
        const secrets = serverDef?.secrets || []
        secrets.forEach((secretVar: any) => {
            properties['secret__' + secretVar.name] = {
                type: "string",
                title: '🔐 Secret: ' + secretVar.name,
                default: "",
                description: `Secret (in env var ${secretVar.env})`
            }
        })

        if (config) {
            config?.properties?.forEach((configVar: any) => {
                const schema = configVar?.Schema || {};
                properties[configVar.Name] = schema
            })
        }

        return {
            type: "object",
            properties: properties,
            required: [],
        }
    }

    const handleSubmit = async ({ formData }: any) => {
        console.log("Connecting to server with data:", formData);

        if (!selectedServer || !selectedServerKey) {
            console.error("No server selected");
            return;
        }

        // create new mcp_server inventory item
        let mcpType;
        let properties: any = {}
        if (selectedServer.type === "server") {
            mcpType = "stdio"
            properties["command"] = "docker"
            properties["args"] = "run --rm -i " + selectedServer.image
        } else if (selectedServer.type === "remote") {
            mcpType = "http"
            properties["url"] = selectedServer.remote.url
        }
        const serverName = "MCP_DOCKER_" + selectedServerKey.toUpperCase()
        const item = {
            name: serverName,
            properties: {
                name: serverName,
                type: mcpType,
                ...properties
            }
        }

        console.log("Creating MCP server inventory item:", item);
        const createdItem = await api.post("/api/inventory/mcp-server", item);
        console.log(createdItem);
    }

    const typeEmojis: { [key: string]: string } = {
        "server": "🖥️",
        "remote": "☁️",
        "poci": "🧪",
    }

    const getTypeEmoji = (type: string) => {
        return typeEmojis[type] || "❓"
    }


    return (
        <div>
            {Object.entries(registry).map(([key, item]: any) => {
                return (
                    <div key={key} className={"border px-4 py-2 mb-4 rounded-xl hover:bg-accent"}>
                        <div className={"flex justify-between items-center"}>
                            <div className={"mb-2"}>
                                <h3 className={"font-bold"} title={item?.description}>
                                    {getTypeEmoji(item.type)} ({item?.type}) {item.title}</h3>
                                <p className={"text-xs text-muted-foreground mb-1 max-h-8 overflow-hidden hover:max-h-16 hover:overflow-y-scroll"}>{item?.description}</p>

                                <div className={"flex flex-row"}>
                                    <div className={"text-xs text-muted-foreground mr-1"}>🛠️ {item?.tools?.length || 0} tools available</div>
                                    <div className={"text-xs text-muted-foreground mr-1"}>{item?.secrets && item?.secrets.length > 0 && ("🔑 Requires secrets")}</div>
                                    <div className={"text-xs text-muted-foreground mr-1"}>{item?.oauth?.providers && item?.oauth?.providers.length > 0
                                        && (`🆔 ${item?.oauth?.providers.length} Oauth provider`)}</div>

                                    <div className={"text-xs text-muted-foreground mr-1"}>
                                        📄 <a rel={"noreferrer noopener"} href={item?.readme} target={"_blank"}>Readme</a>
                                    </div>
                                    <div className={"text-xs text-muted-foreground mr-1"}>
                                        📚 <a rel={"noreferrer noopener"} href={item?.source} target={"_blank"}>Source</a>
                                    </div>
                                </div>
                                <div>
                                    <ReactJson src={item} collapsed={true} />
                                </div>
                            </div>
                            <Button variant={"outline"}
                                    size={"sm"}
                                    onClick={() => {
                                        setSelectedServerKey(key);
                                        setSelectedServer(item);
                                    }}>Connect</Button>
                        </div>
                        {selectedServer?.title === item.title && <div>
                            {item?.tools?.map((tool: any) => (
                                <div key={tool.name}>{tool.name}</div>
                            ))}
                            <Separator className={"my-2"} />
                            <Form schema={buildConnectJsonSchemaForServer(item)}
                                  validator={validator}
                                  onSubmit={handleSubmit}
                            />
                            {result && <ReactJson src={result} />}
                        </div>}
                    </div>
                )
            })}
        </div>
    );
};

export default DockerMcpCatalog;
