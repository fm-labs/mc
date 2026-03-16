import { RJSFSchema } from "@rjsf/utils";
import React, { PropsWithChildren, useContext } from "react";

export type RpcCommandDef = {
    method: string;
    type?: 'action' | 'notification';
    description?: string;
    inputSchema?: RJSFSchema;
    uiSchema?: any;
    outputSchema?: RJSFSchema;
}

type RpcCommandContextType = {
    command: RpcCommandDef
}

const RpcCommandContext = React.createContext<RpcCommandContextType | null>(null)

export const RpcCommandProvider = ({ children, command }: PropsWithChildren<any>) => {
    return (<RpcCommandContext.Provider value={{command}}>
        {children}
    </RpcCommandContext.Provider>)
}

export const useRpcCommand = () => {
    const context = useContext(RpcCommandContext)
    if (!context) {
        throw new Error("useRpcCommand must be used within the RPC command context")
    }
    return context
}
