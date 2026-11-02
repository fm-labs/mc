import React from "react";
import { IconBolt, IconBell, IconTerminal } from "@tabler/icons-react";
import MainContent from "@/components/layout/main-content.tsx";
import { DetailEmpty, ListDetailLayout, SearchableList } from "@/components/layout/list-detail-layout.tsx";
import { RpcCommandDef, RpcCommandProvider } from "@/app/rpc/components/rpc-command-provider.tsx";
import RpcCommand from "@/app/rpc/components/rpc-command.tsx";
import { useApi } from "@/context/api-context.tsx";
import { useSelectedSearchParam } from "@/hooks/use-selected-search-param.ts";
import Header from "@/components/header.tsx";


const RpcPage = () => {
    const { api } = useApi();

    const [commands, setCommands] = React.useState<RpcCommandDef[]>([]);
    const [selectedMethod, setSelectedMethod] = useSelectedSearchParam("method");

    const rpcCommand = React.useMemo(
        () => commands.find((c) => c.method === selectedMethod),
        [commands, selectedMethod],
    );

    const fetchCommands = React.useCallback(async () => {
        try {
            const response = await api.get("/api/rpc");
            setCommands(response || []);
        } catch (error) {
            console.error("Failed to fetch RPC commands:", error);
        }
    }, [api]);

    React.useEffect(() => {
        fetchCommands();
    }, [fetchCommands]);

    const items = React.useMemo(() => commands.map((command) => ({
        id: command.method,
        title: command.method,
        subtitle: command.description,
        icon: command.type === "notification" ? <IconBell size={16} /> : <IconBolt size={16} />,
    })), [commands]);

    return (
        <MainContent>
            <Header title={"Admin RPC"} subtitle={"Run admin RPC commands against your server."} />

            <ListDetailLayout
                list={<SearchableList items={items} selectedId={selectedMethod} onSelect={setSelectedMethod} noun="commands" />}
            >
                {rpcCommand
                    // key resets form/result state when switching commands
                    ? <RpcCommandProvider key={rpcCommand.method} command={rpcCommand}>
                        <RpcCommand />
                    </RpcCommandProvider>
                    : <DetailEmpty icon={<IconTerminal size={32} stroke={1.5} />}>
                        Select a command from the list to see its parameters and run it.
                    </DetailEmpty>}
            </ListDetailLayout>
        </MainContent>
    );
};

export default RpcPage;
