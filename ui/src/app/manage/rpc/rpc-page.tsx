import React from "react";
import { IconBolt, IconBell, IconTerminal } from "@tabler/icons-react";
import MainContent from "@/components/layout/main-content.tsx";
import { DetailEmpty, ListDetailLayout, SearchableList } from "@/components/layout/list-detail-layout.tsx";
import { RpcCommandDef, RpcCommandProvider } from "@/app/manage/rpc/components/rpc-command-provider.tsx";
import RpcCommand from "@/app/manage/rpc/components/rpc-command.tsx";
import { useApi } from "@/context/api-context.tsx";
import { useSelectedSearchParam } from "@/hooks/use-selected-search-param.ts";
import Header from "@/components/header.tsx";
import {ContainerHostsProvider} from "@/app/containers/components/container-hosts-provider.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import {useParams} from "react-router";
import { nodeHeaders } from "@/lib/node-headers.ts";


const RpcView = ({hostId}: {hostId?: string}) => {
    const { api } = useApi();

    const [commands, setCommands] = React.useState<RpcCommandDef[]>([]);
    const [selectedMethod, setSelectedMethod] = useSelectedSearchParam("method");

    const rpcCommand = React.useMemo(
        () => commands.find((c) => c.method === selectedMethod),
        [commands, selectedMethod],
    );

    const fetchCommands = React.useCallback(async () => {
        setCommands([]);
        try {
            const response = await api.get("/api/rpc", { headers: nodeHeaders(hostId) });
            setCommands(response || []);
        } catch (error) {
            console.error("Failed to fetch RPC commands:", error);
        }
    }, [api, hostId]);

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
        <>
            <ListDetailLayout
                list={<SearchableList items={items} selectedId={selectedMethod} onSelect={setSelectedMethod} noun="commands" />}
            >
                {rpcCommand
                    // key resets form/result state when switching commands or hosts
                    ? <RpcCommandProvider key={`${hostId}/${rpcCommand.method}`} command={rpcCommand}>
                        <RpcCommand hostId={hostId} />
                    </RpcCommandProvider>
                    : <DetailEmpty icon={<IconTerminal size={32} stroke={1.5} />}>
                        Select a command from the list to see its parameters and run it.
                    </DetailEmpty>}
            </ListDetailLayout>
        </>
    );
};

const RpcPage = () => {
    const {hostId} = useParams<{ hostId: string }>();
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return <ContainerHostsProvider>
        <ContainersLayout>
            <MainContent>
                <Header title={"Admin RPC"} subtitle={`Run admin RPC commands on ${hostId}.`} />
                <RpcView hostId={hostId} />
            </MainContent>
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default RpcPage;
