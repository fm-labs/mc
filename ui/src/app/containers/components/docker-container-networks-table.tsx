import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { KeyValueTable } from "@/components/key-value-table.tsx";

const DockerContainerNetworksTable = () => {
    const { container } = useDockerContainer()
    const networks = container?.NetworkSettings?.Networks;

    return (
        <div>
            {networks &&
                Object.entries(networks).map(([key, network]: [string, any]) => {
                    const kvData = Object.entries(network).map((entry) => {
                        return {
                            key: entry[0],
                            value: entry[1],
                        };
                    });
                    return <div key={key}>
                        <h3 className={"font-bold text-xl mb-2 px-2"}>Network {key}</h3>
                        <KeyValueTable data={kvData} />
                    </div>

                    // return (
                    //     <div key={key}>
                    //         <div style={{ fontWeight: 'bold' }}>Network: {key}</div>
                    //         <div>IP Address: {network.IPAddress}</div>
                    //         <div>Gateway: {network.Gateway}</div>
                    //         <div>Mac Address: {network.MacAddress}</div>
                    //         <div>Aliases: {network.Aliases.join(', ')}</div>
                    //         {/*<div>DriverOpts: {network.DriverOpts}</div>*/}
                    //         <div>NetworkID: {network.NetworkID}</div>
                    //         <div>EndpointID: {network.EndpointID}</div>
                    //         {/*<div>IPAMConfig: {network.IPAMConfig}</div>*/}
                    //         {/*<div>Links: {network.Links}</div>*/}
                    //         <div>DNSNames: {network?.DNSNames?.join(', ')}</div>
                    //     </div>
                    // )
                })}
        </div>
    );
};

export default DockerContainerNetworksTable;
