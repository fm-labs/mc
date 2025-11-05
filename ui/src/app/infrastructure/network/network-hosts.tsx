import { useNetwork } from "@/app/infrastructure/network/network-provider.tsx";
import { HostStatus } from "@/app/infrastructure/host/host-status.tsx";
import { Link } from "react-router";
import { HostProvider } from "@/app/infrastructure/host/host-provider.tsx";

const NetworkHosts = () => {
    const hosts = useNetwork();

    if (!hosts) {
        return <div>No hosts</div>;
    }

    return (
        <div>
            {hosts && hosts.hosts.map((host) => (
                <div key={host.id} className="flex items-center justify-between border-b py-2">
                    <HostProvider host={host}>
                        <div>
                            <HostStatus />{" "}
                            <Link to={`/infrastructure/host/${host.item_key}`}>{host.name}</Link>
                        </div>
                        <div>{host?.properties?.ipAddress}</div>
                    </HostProvider>
                </div>
            ))}
        </div>
    );
};

export default NetworkHosts;
