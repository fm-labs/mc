import React, {type ChangeEvent, useState} from 'react'
import {Badge} from "@/components/ui/badge.tsx";
import {Input} from "@/components/ui/input.tsx";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select.tsx";
import {ArrowDownAZ, ArrowUpAZ, ImageIcon, SlidersHorizontal, TagIcon} from "lucide-react";
import {Separator} from "@/components/ui/separator.tsx";
import AppIcon from "@/components/app-icon.tsx";
import {Button} from "@/components/ui/button.tsx";
import {useApi} from "@/context/api-context.tsx";
import useDialog from "@/hooks/use-dialog.tsx";
import Data from "@/components/data.tsx";
import MyForm from "@/components/rjsf/my-form.tsx";
import {RJSFSchema} from "@rjsf/utils";

interface PortainerTemplatesViewProps {
    templateUrl: string
}

const PortainerTemplateInfoDialog = ({template}: any) => {

    const templateSchema: RJSFSchema = React.useMemo(() => {

        const properties: any = {};
        // map portainer env variables to form properties
        template?.env?.forEach((envVar: any) => {
            properties[envVar.name] = {
                type: envVar.type === 'boolean' ? 'boolean' : 'string',
                title: envVar.label || envVar.name,
                default: envVar.default || '',
                description: envVar.description || '',
            }

            if (envVar?.select) {
                properties[envVar.name].enum = envVar.select.map((option: any) => option.value);
                const defaultSelect = envVar.select.find((option: any) => option?.default === true);
                if (defaultSelect) {
                    properties[envVar.name].default = defaultSelect.value;
                }
            }
        });

        return {
            type: "object",
            properties: properties
        }
    }, [template]);

    return (
        <div>
            <h2>{template?.title}
                <Data data={template}/>
            </h2>
            <div className={''}>
                <MyForm schema={templateSchema}/>
            </div>
        </div>
    )
}

const PortainerTemplateTypeBadge = ({type}: { type: number }) => {
    const chipProps: any = {
        size: 'small',
        color: 'info',
        variant: 'outlined',
    }
    switch (type) {
        case 1:
            return <Badge {...chipProps} title={'container'}>container</Badge>
        case 2:
            return <Badge {...chipProps} title={'stack'}>stack</Badge>
        case 3:
            return <Badge {...chipProps} title={'compose'}>compose</Badge>
        default:
            return <Badge {...chipProps} color={'error'} title={'unknown'}>unknown</Badge>
    }
}

const PortainerTemplatesView = ({templateUrl}: PortainerTemplatesViewProps) => {
    const [templates, setTemplates] = React.useState<any[]>([])

    const fetchTemplates = React.useCallback(async () => {
        const response = await fetch(templateUrl)
        const data = await response.json()
        console.log('templates data', data)
        setTemplates(data?.templates || [])
    }, [templateUrl])

    // const handleLaunchTemplate = (template: any) => {
    //   console.log('launch template', template)
    //   api.launchPortainerTemplate(template)
    // }

    React.useEffect(() => {
        fetchTemplates()
    }, [templateUrl])


    //const navigate = useNavigate();
    const {api} = useApi();
    const {createDialog} = useDialog();

    const [currentTemplate, setCurrentTemplate] = useState<any>(null);

    const query = new URLSearchParams(window.location.search);
    const searchTermQuery = query.get("filter") || "";
    const typeQuery = (query.get("type")) || "all";
    const sortQuery = (query.get("sort") as "asc" | "desc") || "asc";

    const [sort, setSort] = useState(sortQuery);
    const [typeFilter, setTypeFilter] = useState(typeQuery);
    const [searchTerm, setSearchTerm] = useState(searchTermQuery);

    const filteredTemplates = templates
        .sort((a: any, b: any) =>
            sort === "asc"
                ? a.title.localeCompare(b.title)
                : b.title.localeCompare(a.title),
        )
    // .filter((app) =>
    //     appType==="installed"
    //         ? app.installed
    //         :appType==="notDeployed"
    //             ? !app.installed
    //             :true,
    // )
    // .filter((app) => app.title.toLowerCase().includes(searchTerm.toLowerCase()));

    const handleSearch = (e: ChangeEvent<HTMLInputElement>) => {
        setSearchTerm(e.target.value);
        // navigate({
        //   search: (prev: any) => ({
        //     ...prev,
        //     filter: e.target.value || undefined,
        //   }),
        // })
    };

    const handleTypeChange = (value: string) => {
        setTypeFilter(value);
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

    const handleDeployClick = (app: any) => async () => {
        // Handle connect logic here
        console.info(`Deploying to ${app.title}...`);
        setCurrentTemplate(app);
    };

    const onDeploySubmit = async () => {
        // For example, you might call an API to connect
        try {
            //await api.post(`/api/templates/${app.title}/connect`);
            fetchTemplates(); // Refresh the list after connecting
        } catch (error) {
            console.error("Error connecting:", error);
        }
    };


    if (!templates) {
        return <div>Loading...</div>
    }

    return (
        <>
            <div>
                <div className="my-4 flex items-end justify-between sm:my-0 sm:items-center">
                    <div className="flex flex-col gap-4 sm:my-4 sm:flex-row">
                        <Input
                            placeholder="Filter apps..."
                            className="h-9 w-40 lg:w-[250px]"
                            value={searchTerm}
                            onChange={handleSearch}
                        />
                        <Select value={typeFilter} onValueChange={handleTypeChange}>
                            <SelectTrigger className="w-36">
                                <SelectValue>{typeFilter}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Apps</SelectItem>
                                <SelectItem value="installed">Deployed</SelectItem>
                                <SelectItem value="notDeployed">Not Deployed</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <Select value={sort} onValueChange={handleSortChange}>
                        <SelectTrigger className="w-16">
                            <SelectValue>
                                <SlidersHorizontal size={18}/>
                            </SelectValue>
                        </SelectTrigger>
                        <SelectContent align="end">
                            <SelectItem value="asc">
                                <div className="flex items-center gap-4">
                                    <ArrowUpAZ size={16}/>
                                    <span>Ascending</span>
                                </div>
                            </SelectItem>
                            <SelectItem value="desc">
                                <div className="flex items-center gap-4">
                                    <ArrowDownAZ size={16}/>
                                    <span>Descending</span>
                                </div>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <Separator className="shadow-sm"/>
                <ul className="faded-bottom no-scrollbar grid gap-4 overflow-auto pt-4 pb-16 md:grid-cols-2 lg:grid-cols-3">
                    {filteredTemplates.map((template: any, idx) => (
                        <li
                            key={template.title + idx}
                            className="rounded-lg border p-4 hover:shadow-md"
                        >
                            <div className="mb-8 flex items-center justify-between">

                                {template?.logo
                                    ? <img src={template?.logo} alt={template?.title} className="h-10"/>
                                    :
                                    <div className={`bg-muted flex size-10 items-center justify-center rounded-lg p-2`}
                                    ><AppIcon icon={"rocket"}/></div>}

                                <Button
                                    variant="outline"
                                    size="sm"
                                    className={`${template.installed ? "border border-blue-300 bg-blue-50 hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-950 dark:hover:bg-blue-900" : ""}`}
                                    onClick={handleDeployClick(template)}
                                >
                                    Launch
                                </Button>
                            </div>
                            <div>
                                <h2 className="mb-1 font-semibold">{template.title} <Data data={template}/></h2>
                                <p className="line-clamp-2 mb-2 text-gray-500">{template.description}</p>
                                <div className={"mb-2 text-sm flex gap-1"}>
                                    {template?.categories?.map((c: string) => <Badge key={c}
                                                                                     variant={"outline"}><TagIcon/> {c}
                                    </Badge>)}
                                </div>
                                <div className={"mb-1 text-sm flex gap-1"}>
                                    <PortainerTemplateTypeBadge type={template.type}/>
                                    {template?.interactive && <Badge variant={"outline"}>interactive</Badge>}
                                    {template?.env?.length > 0 &&
                                        <Badge variant={"outline"}>{template?.env?.length} env vars</Badge>}
                                    {template?.volumes?.length > 0 &&
                                        <Badge variant={"outline"}>{template?.volumes?.length} volumes</Badge>}
                                    {template?.ports?.length > 0 &&
                                        <Badge variant={"outline"}>{template?.ports?.length} ports</Badge>}

                                </div>
                                <div>
                                    {template?.type === 1 &&
                                        <Badge variant={"outline"}><ImageIcon/> {template?.image}</Badge>}
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {currentTemplate && (
                createDialog({
                    title: `Deploy ${currentTemplate.title}`,
                    children: <PortainerTemplateInfoDialog template={currentTemplate}/>,
                    onClose: () => setCurrentTemplate(null),
                })
            )}

        </>
    );
}

export default PortainerTemplatesView
