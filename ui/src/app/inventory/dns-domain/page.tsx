import React from "react";
import { useLoaderData, useNavigate } from "react-router";
import { toast } from "sonner";
import TaskButton from "@/components/task-button.tsx";
import { Button } from "@/components/ui/button.tsx";
import { useApi } from "@/context/api-context.tsx";
import { FEAT_DOMAIN_VIEWS_ENABLED, FEAT_DOMAIN_WEBCHECK_ENABLED } from "@/constants.ts";

const DomainsPage = () => {
    if (!FEAT_DOMAIN_VIEWS_ENABLED) {
        return <div className={"p-4"}>Domain views feature is disabled.</div>;
    }

    const data = useLoaderData()
    const navigate = useNavigate()
    const { api } = useApi()

    const resultRef = React.useRef<HTMLDivElement>(null);

    const handleAction = (item: any, action: string) => async () => {
        if (resultRef.current) {
            resultRef.current.innerText = `Submitting ${action} action for ${item.name}...`;
        }

        return api.submitDomainAction()(item, action).then((response: any) => {
            console.log(`${action} action response for ${item.name}`, response);
            toast.info(action)
            if (resultRef.current) {
                resultRef.current.innerText = JSON.stringify(response, null, 2);
            }
            return response
        })
    }

    const handleOnSuccess = (result: any) => {
        console.log("Action success", result);
        toast.success("Action completed successfully");

        // check if result is string or object
        if (typeof result === 'string') {
            if (resultRef.current) {
                resultRef.current.innerText = result;
            }
            return;
        } else if (typeof result === 'object') {
            if (resultRef.current) {
                resultRef.current.innerText = JSON.stringify(result, null, 2);
            }
            return;
        } else {
            if (resultRef.current) {
                resultRef.current.innerText = "Unknown result type";
            }
            return;
        }
    }

    React.useEffect(() => {
        if (resultRef.current) {
            resultRef.current.innerText = "";
        }
    }, [])

    return (
        <div className={"p-4"}>
            {data && data.length > 0 && data.map((item: any) => {
                return <div key={item.name} className={"border-b flex flex-row justify-between items-center py-2"}>
                    {item.name}
                    <div className={"flex gap-1 mt-1"}>
                        <TaskButton label={'Ping'} promise={handleAction(item, 'ping')} onSuccess={handleOnSuccess}>Ping</TaskButton>
                        <TaskButton label={'Whois'} promise={handleAction(item, 'whois')} onSuccess={handleOnSuccess}>Whois</TaskButton>
                        <TaskButton label={'Dig'} promise={handleAction(item, 'dig')} onSuccess={handleOnSuccess}>dig</TaskButton>

                        {FEAT_DOMAIN_WEBCHECK_ENABLED &&
                        <Button variant={"outline"} onClick={() => navigate('webcheck/' + item.name)}>webcheck</Button>}
                    </div>
                </div>
            })}
            <div ref={resultRef}></div>
        </div>
    );
};

export default DomainsPage;
