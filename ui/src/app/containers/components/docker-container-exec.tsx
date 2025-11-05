import React from "react";
import { toast } from "react-toastify";
import { useDockerContainer } from "@/app/containers/components/docker-container-provider.tsx";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";


const DockerContainerExec = () => {
    const { container, hostId } = useDockerContainer();
    const { api } = useApi();

    const [response, setResponse] = React.useState<any>([]);
    const [command, setCommand] = React.useState("whoami");

    const outputLines: string[] = React.useMemo(() => {
        return response?.output ? response.output.split("\n") : [];
    }, [response?.output]);

    const execCommand = React.useCallback(async () => {
        if (!container) {
            toast.error("Container not found");
            return;
        }
        if (!command) {
            toast.error("Command is empty");
            return;
        }

        api.post(`/api/containers/${hostId}/containers/${container.Id}/exec`, { command })
            .then((response: any) => {
                console.log(response);
                setResponse(response);
            })
            .catch((error: any) => {
                setResponse({
                    output: "An error occured\n" + (error?.message || "Unknown error"),
                });
            });
    }, [container, command, api, setResponse, hostId]);

    return (
        <div>
            <div>
                {outputLines.map((line, index) => (
                    <div key={index}>{line}</div>
                ))}
            </div>
            <div>
        <textarea
            style={{ maxWidth: "800px" }}
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            cols={100}
            rows={3}
        />
            </div>
            <div>
                <Button onClick={execCommand} variant={"outline"}>
                    Execute
                </Button>
            </div>
        </div>
    );
};

export default DockerContainerExec;
