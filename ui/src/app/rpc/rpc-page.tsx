import React from "react";
import MainContent from "@/components/layout/main-content.tsx";
import { useState } from "react";
import { RpcCommandDef, RpcCommandProvider } from "@/app/rpc/components/rpc-command-provider.tsx";
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


const RpcPage = () => {
    const {api} = useApi();

    //const commands = rpcCommands as RpcCommandDef[];
    const [commands, setCommands] = useState<RpcCommandDef[]>([]);
    const [rpcCommand, setRpcCommand] = useState<RpcCommandDef>()

    const handleSelectChange = (selected: string) => {
        const selectedCommand = commands.find((c) => c.method === selected);
        setRpcCommand(selectedCommand);
    }

    const fetchCommands = async () => {
        try {
            const response = await api.get("/api/rpc");
            console.log("Fetched RPC commands:", response);
            setCommands(response);
        } catch (error) {
            console.error("Failed to fetch RPC commands:", error);
        }
    }

    React.useEffect(() => {
        fetchCommands();
    }, []);

    return (
        <>
            <MainContent>
                <div>
                    <h1 className="text-2xl font-bold">Admin RPC</h1>
                    <p className="mb-4 text-muted-foreground">
                        Administrative gameserver controls
                    </p>
                </div>
                <div>
                    <Select onValueChange={handleSelectChange}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select a command" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectLabel>Available commands</SelectLabel>
                                {commands.map((command) => (
                                    <SelectItem key={command.method} value={command.method}>{command.method}</SelectItem>
                                ))}
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>
                <hr />
                <div>
                    {rpcCommand && <RpcCommandProvider command={rpcCommand}>
                        <RpcCommand />
                    </RpcCommandProvider>}
                </div>
            </MainContent>
        </>
    );
};

export default RpcPage;
