/**
 * Container mounts
 *
 *  "Mounts": [
 *    {
 *      "Type": "bind",
 *      "Source": "/home/user/data/postgres",
 *      "Destination": "/var/lib/postgresql/data",
 *      "Mode": "rw",
 *      "RW": true,
 *      "Propagation": "rprivate"
 *    }
 *    "Mounts": [
 *      {
 *        "Type": "volume",
 *        "Source": "kontainer-core_kontainer_agent_data",
 *        "Target": "/app/data",
 *        "VolumeOptions": {}
 *      }
 *    ],
 *  ],
 * @param mounts
 * @constructor
 */

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";

export const DockerContainerMountsTable = () => {
    const { container } = useDockerContainer();
    const mounts: any[] = container?.Mounts;


    return (
        <div>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Destination</TableHead>
                        <TableHead>Mode</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {mounts
                        .sort((a, b) => {
                            if (a.Destination < b.Destination) {
                                return -1;
                            }
                            if (a.Destination > b.Destination) {
                                return 1;
                            }
                            return 0;
                        })
                        .map((mount, index) => (
                            <TableRow key={`mount-${index}`}>
                                <TableCell>{mount?.Type}</TableCell>
                                <TableCell>{mount?.Source}</TableCell>
                                <TableCell>{mount?.Destination}</TableCell>
                                <TableCell>{mount?.Mode}</TableCell>
                            </TableRow>
                        ))}
                </TableBody>
            </Table>
        </div>
    );
};
