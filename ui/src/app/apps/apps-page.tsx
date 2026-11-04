import {Link, useLoaderData, useNavigate, useParams} from "react-router";
import MainContent from "@/components/layout/main-content.tsx";
import Header from "@/components/header.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table.tsx";
import { AppSpec } from "@/features/apps/apps.types.ts";
import {ContainerHostsProvider} from "@/app/containers/components/container-hosts-provider.tsx";
import ContainersLayout from "@/components/layout/containers-layout.tsx";
import React from "react";

const AppsPageView = ({hostId}: {hostId?: string}) => {
    const apps = (useLoaderData() as AppSpec[] | null) || [];
    const navigate = useNavigate();

    return (
        <MainContent>
            <Header title="Apps" subtitle="App specs stored in the mc config dir.">
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => navigate(`/manage/${hostId}/apps/new?source=bundle`)}>From bundle</Button>
                    <Button onClick={() => navigate(`/manage/${hostId}/apps/new`)}>New app</Button>
                </div>
            </Header>
            {apps.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                    No apps yet. <Link to="/manage/${hostId}/apps/new" className="text-primary hover:underline">Create one</Link> from a compose.yaml or <Link to="/manage/${hostId}/apps/new?source=bundle" className="text-primary hover:underline">a bundle</Link>.
                </p>
            ) : (
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Id</TableHead>
                            <TableHead>Title</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Description</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {apps.map((app) => (
                            <TableRow
                                key={app.id}
                                className="cursor-pointer"
                                onClick={() => navigate(`/manage/${hostId}/apps/${encodeURIComponent(app.id)}`)}
                            >
                                <TableCell className="font-mono">{app.id}</TableCell>
                                <TableCell>{app.title || "-"}</TableCell>
                                <TableCell><Badge variant="outline">{app.type}</Badge></TableCell>
                                <TableCell className="text-muted-foreground">{app.description || ""}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}
        </MainContent>
    );
};

const AppsPage = () => {
    const {hostId} = useParams<{ hostId: string }>();
    if (!hostId) {
        return <div className={"p-4"}>Host ID missing</div>;
    }

    return <ContainerHostsProvider>
        <ContainersLayout>
            <AppsPageView hostId={hostId} />
        </ContainersLayout>
    </ContainerHostsProvider>;
};

export default AppsPage;
