import React from "react";
import { useHost } from "@/app/infrastructure/host/host-provider.tsx";

const HostServices = () => {
    const { host, services, fetchServices } = useHost()

    React.useEffect(() => {
        fetchServices()
    }, [])

    return (
        <div>
            <h2 className="text-lg font-medium mb-4">Services on {host.name}</h2>
            <button
                onClick={fetchServices}
                className="mb-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
                Refresh Services
            </button>
            <div>
                {/* Render services here */}
                {services && services.length > 0 && (
                    <ul className="space-y-2">
                        {services.map((service) => (
                            <li key={service.name} className="p-4 border rounded shadow-sm">
                                <h3 className="text-md font-semibold">{service.name}</h3>
                                <div className={"text-sm text-muted-foreground"}>{service.item_type}</div>
                                <p>Status: <span className={service.status === 'running' ? 'text-green-600' : 'text-red-600'}>{service.status || "unknown"}</span></p>
                                {service.description && <p>Description: {service.description}</p>}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default HostServices;
