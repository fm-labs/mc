import React, { type ChangeEvent, useState } from "react";
import { SlidersHorizontal, ArrowUpAZ, ArrowDownAZ } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import MainContent from "@/components/layout/main-content.tsx";
import { useApi } from "@/context/api-context.tsx";
import AppIcon from "@/components/app-icon.tsx";
import useDialog from "@/hooks/use-dialog.tsx";
import Form from "@rjsf/shadcn";
import validator from "@rjsf/validator-ajv8";
import { FEAT_INTEGRATIONS_ENABLED } from "@/constants.ts";

type AppType = "all" | "connected" | "notConnected"

const appText = new Map<AppType, string>([
    ["all", "All Apps"],
    ["connected", "Connected"],
    ["notConnected", "Not Connected"],
]);


const IntegrationConnectForm = ({ onConnect }: { app: any, onConnect: () => void }) => {
    const schema = {
        type: "object",
        properties: {
            apiKey: { type: "string", title: "API Key" },
            apiSecret: { type: "string", title: "API Secret" },
        },
        required: ["apiKey", "apiSecret"],
    }

    return (
        <div>
            <Form schema={schema} validator={validator} onSubmit={onConnect}>
                <div className="mt-4 flex justify-end">
                    <Button type="submit">Connect</Button>
                </div>
            </Form>
        </div>
    );
};


export function IntegrationsPage() {
    if (!FEAT_INTEGRATIONS_ENABLED) {
        return <div className={"p-4"}>Integrations feature is disabled.</div>;
    }

    //const navigate = useNavigate();
    const { api } = useApi();
    const { createDialog } = useDialog();
    const [integrations, setIntegrations] = useState<any[]>([]);

    const [currentIntegration, setCurrentIntegration] = useState<any>(null);

    const query = new URLSearchParams(window.location.search);
    const filter = query.get("filter") || "";
    const type = (query.get("type") as AppType) || "all";
    const initSort = (query.get("sort") as "asc" | "desc") || "asc";

    const [sort, setSort] = useState(initSort);
    const [appType, setAppType] = useState(type);
    const [searchTerm, setSearchTerm] = useState(filter);

    const fetchIntegrations = async () => {
        try {
            const response = await api.get("/api/integrations");
            setIntegrations(response);
            return response;
        } catch (error) {
            console.error("Error fetching integrations:", error);
            return [];
        }
    };

    const filteredApps = integrations
        .sort((a, b) =>
            sort==="asc"
                ? a.name.localeCompare(b.name)
                :b.name.localeCompare(a.name),
        )
        .filter((app) =>
            appType==="connected"
                ? app.connected
                :appType==="notConnected"
                    ? !app.connected
                    :true,
        )
        .filter((app) => app.name.toLowerCase().includes(searchTerm.toLowerCase()));

    const handleSearch = (e: ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        // navigate({
        //   search: (prev: any) => ({
        //     ...prev,
        //     filter: e.target.value || undefined,
        //   }),
        // })
    };

    const handleTypeChange = (value: AppType) => {
        setAppType(value);
        // navigate({
        //   search: (prev: any) => ({
        //     ...prev,
        //     type: value === 'all' ? undefined : value,
        //   }),
        // })
    };

    const handleSortChange = (sort: "asc" | "desc") => {
        setSort(sort);
        //navigate({ search: (prev: any) => ({ ...prev, sort }) })
    };

    const handleConnectClick = (app: any) => async () => {
        // Handle connect logic here
        console.info(`Connecting to ${app.name}...`);
        setCurrentIntegration(app);
    };

    const onConnectSubmit = async () => {
        // For example, you might call an API to connect
        try {
            //await api.post(`/api/integrations/${app.name}/connect`);
            fetchIntegrations(); // Refresh the list after connecting
        } catch (error) {
            console.error("Error connecting:", error);
        }
    };

    React.useEffect(() => {
        fetchIntegrations();
    }, []);

    return (
        <>
            {/* ===== Content ===== */}
            <MainContent>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">
                        App Integrations
                    </h1>
                    <p className="text-muted-foreground">
                        Here&apos;s a list of your apps for the integration!
                    </p>
                </div>
                <div className="my-4 flex items-end justify-between sm:my-0 sm:items-center">
                    <div className="flex flex-col gap-4 sm:my-4 sm:flex-row">
                        <Input
                            placeholder="Filter apps..."
                            className="h-9 w-40 lg:w-[250px]"
                            value={searchTerm}
                            onChange={handleSearch}
                        />
                        <Select value={appType} onValueChange={handleTypeChange}>
                            <SelectTrigger className="w-36">
                                <SelectValue>{appText.get(appType)}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Apps</SelectItem>
                                <SelectItem value="connected">Connected</SelectItem>
                                <SelectItem value="notConnected">Not Connected</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <Select value={sort} onValueChange={handleSortChange}>
                        <SelectTrigger className="w-16">
                            <SelectValue>
                                <SlidersHorizontal size={18} />
                            </SelectValue>
                        </SelectTrigger>
                        <SelectContent align="end">
                            <SelectItem value="asc">
                                <div className="flex items-center gap-4">
                                    <ArrowUpAZ size={16} />
                                    <span>Ascending</span>
                                </div>
                            </SelectItem>
                            <SelectItem value="desc">
                                <div className="flex items-center gap-4">
                                    <ArrowDownAZ size={16} />
                                    <span>Descending</span>
                                </div>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <Separator className="shadow-sm" />
                <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 md:grid-cols-2 lg:grid-cols-3">
                    {filteredApps.map((app) => (
                        <li
                            key={app.name}
                            className="rounded-lg border p-4 hover:shadow-md"
                        >
                            <div className="mb-8 flex items-center justify-between">
                                <div
                                    className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
                                >
                                    <AppIcon icon={app.name} />
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className={`${app.connected ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900":""}`}
                                    onClick={handleConnectClick(app)}
                                >
                                    {app.connected ? "Connected":"Connect"}
                                </Button>
                            </div>
                            <div>
                                <h2 className="mb-1 font-semibold">{app.name}</h2>
                                <p className="line-clamp-2 text-gray-500">{app.desc}</p>
                            </div>
                        </li>
                    ))}
                </ul>
            </MainContent>
            {currentIntegration && createDialog({
                title: `Connect to ${currentIntegration.name}`,
                children: <IntegrationConnectForm
                    app={currentIntegration}
                    onConnect={() => {
                        onConnectSubmit();
                    }} />,
                onClose: () => setCurrentIntegration(null),
            })}
        </>
    );
}
