import React from "react";
import { IconRefresh } from "@tabler/icons-react";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table.tsx";

type ContainerTop = {
    Titles: string[];
    Processes: string[][];
};

// Running processes of a container (`docker top`), from GET /containers/{host}/containers/{id}/top
const DockerContainerTop = () => {
    const { container, hostId } = useDockerContainer();
    const { api } = useApi();

    const [top, setTop] = React.useState<ContainerTop>();
    const [error, setError] = React.useState<string>();
    const [loading, setLoading] = React.useState(false);
    const [psArgs, setPsArgs] = React.useState("");

    const isRunning = container?.State?.Running === true;

    const fetchTop = React.useCallback(() => {
        if (!container?.Id || !isRunning) {
            return;
        }
        setLoading(true);
        setError(undefined);
        const params = psArgs.trim() ? { ps_args: psArgs.trim() } : undefined;
        api.get(`/api/containers/${hostId}/containers/${container.Id}/top`, { params })
            .then((data: ContainerTop) => setTop(data))
            .catch((err: any) => {
                setTop(undefined);
                setError(err?.response?.data?.detail || err?.message || "Unknown error");
            })
            .finally(() => setLoading(false));
    }, [api, hostId, container?.Id, isRunning, psArgs]);

    // load once when the tab opens; later refreshes are manual
    React.useEffect(() => {
        fetchTop();
    },[hostId, container?.Id, isRunning]);

    if (!isRunning) {
        return <div className={"p-2 text-muted-foreground"}>The container is not running.</div>;
    }

    return (
        <div className={"space-y-2"}>
            <form className={"flex items-center gap-2"}
                  onSubmit={(e) => {
                      e.preventDefault();
                      fetchTop();
                  }}>
                <Input className={"h-8 max-w-[200px]"}
                       placeholder={"ps args, e.g. aux"}
                       value={psArgs}
                       onChange={(e) => setPsArgs(e.target.value)} />
                <Button type={"submit"} variant={"outline"} size={"sm"} disabled={loading}>
                    <IconRefresh size={"1em"} className={loading ? "animate-spin" : ""} /> Refresh
                </Button>
            </form>

            {error && <div className={"text-destructive"}>{error}</div>}
            {!error && !top && loading && <div>Loading ...</div>}

            {top && (
                <Table>
                    <TableHeader>
                        <TableRow>
                            {top.Titles.map((title) => <TableHead key={title}>{title}</TableHead>)}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {top.Processes.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={top.Titles.length} className={"text-muted-foreground"}>
                                    No processes.
                                </TableCell>
                            </TableRow>
                        )}
                        {top.Processes.map((row, rowIndex) => (
                            <TableRow key={rowIndex}>
                                {row.map((value, colIndex) => (
                                    <TableCell key={colIndex}
                                               className={colIndex === row.length - 1 ? "font-mono whitespace-pre-wrap break-all" : "font-mono"}>
                                        {value}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}
        </div>
    );
};

export default DockerContainerTop;
