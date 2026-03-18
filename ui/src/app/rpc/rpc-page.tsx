import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import {useState} from "react";
import {RpcCommandDef, RpcCommandProvider} from "@/app/rpc/components/rpc-command-provider.tsx";
import {
    Select,
    SelectContent,
    SelectGroup, SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select.tsx";
import RpcCommand from "@/app/rpc/components/rpc-command.tsx";
import {useApi} from "@/context/api-context.tsx";
import Header from "@/components/header.tsx";
import SectionCard from "@/components/section-card.tsx";


const RpcPage = () => {
    const {api} = useApi();

    //const commands = rpcCommands as RpcCommandDef[];
    const [commands, setCommands] = useState<RpcCommandDef[]>([]);
    const [rpcCommand, setRpcCommand] = useState<RpcCommandDef>()

    const handleSelectChange = (selected: string) => {
        const selectedCommand = commands.find((c) => c.method === selected);
        setRpcCommand(selectedCommand);
    }

    const fetchCommands = React.useCallback(async () => {
        try {
            const response = await api.get("/api/rpc");
            console.log("Fetched RPC commands:", response);
            setCommands(response);
        } catch (error) {
            console.error("Failed to fetch RPC commands:", error);
        }
    }, [api]);

    React.useEffect(() => {
        fetchCommands();
    }, [fetchCommands]);

    return (
        <>
            <MainContent>
                <div>
                    <Header title={"Admin RPC"} subtitle={'Run admin RPC commands against your server.'}/>
                    <p className="mb-4 text-muted-foreground">
                        Select a command from the dropdown.
                    </p>
                </div>

                <SectionCard title={"Execute RPC Command"}>
                    <div>
                        <Select onValueChange={handleSelectChange}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Select a command"/>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    <SelectLabel>Available commands</SelectLabel>
                                    {commands.map((command) => (
                                        <SelectItem key={command.method}
                                                    value={command.method}>{command.method}</SelectItem>
                                    ))}
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        {rpcCommand && <RpcCommandProvider command={rpcCommand}>
                            <hr className={"my-4"}/>
                            <RpcCommand/>
                        </RpcCommandProvider>}
                    </div>
                </SectionCard>
            </MainContent>
        </>
    );
};

export default RpcPage;
