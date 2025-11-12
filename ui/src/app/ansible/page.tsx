import React from "react";
import { useOrchestraApi } from "@/app/ansible/use-orchestra-api.ts";
import AppIcon from "@/components/app-icon.tsx";
import { formatDistanceToNow } from "date-fns";
import { EventSourceReader } from "@/components/event-source-reader.tsx";
import { FEAT_ANSIBLE_ENABLED } from "@/constants.ts";
import { useApi } from "@/context/api-context.tsx";
import AnsibleRunnerStats from "@/app/ansible/components/ansible-runner-stats.tsx";
import {Badge} from "@/components/ui/badge.tsx";


type Job = {
    run_id: string;
    project_path: string;
    playbook: string;
    created_at: number; // unix
    status: "successful" | "failed" | "initialized" | "running" | string;
    events?: any[];
    stdout?: string;
    stderr?: string;
    stats?: any
};

const statusClasses = (status: string) => {
    switch (status) {
        case "successful":
            return "text-green-700 border-green-300 bg-green-50";
        case "failed":
            return "text-red-700 border-red-300 bg-red-50";
        case "initialized":
        case "running":
            return "text-sky-700 border-sky-300 bg-sky-50";
        default:
            return "text-gray-700 border-gray-300 bg-gray-50";
    }
};

const JobStatus = ({ status }: { status: string }) => (
    <Badge
        variant={"outline"}
        className={`text-sm ${statusClasses(
            status,
        )}`}
    >
    {status}
  </Badge>
);

const JobEvent = ({ event }: { event: any }) => {
    const [open, setOpen] = React.useState(false);

    return (
        <div className="max-w border-b border-gray-200 p-2">
            <div className="flex items-center justify-between gap-2">
                <div className="text-sm text-gray-800"
                     onClick={() => setOpen(!open)}>
                    <span className="font-mono">#{event.counter}</span>{" "}
                    {event.event}
                </div>
            </div>

            {open && (
                <div className="mt-2 rounded-md bg-gray-50 p-2">
          <pre className="whitespace-pre-wrap break-words text-xs text-gray-800">
            {JSON.stringify(event, null, 2)}
          </pre>
                </div>
            )}
        </div>
    );
};

const OrchestraJobsPage = () => {
    if (!FEAT_ANSIBLE_ENABLED) {
        return <div className={"p-4"}>Ansible feature is disabled.</div>
    }

    const { apiBaseUrl } = useApi()
    const api = useOrchestraApi(apiBaseUrl);
    const [jobs, setJobs] = React.useState<Job[]>([]);
    const [job, setJob] = React.useState<Job | null>(null);

    const jobEventSourceUrl = React.useMemo(() => job
        ? `${apiBaseUrl}/api/ansible/runs/${job.run_id}/sse`:null
    , [job]);

    const handleJobClick = async (jobId: string) => {
        try {
            const jobDetails = await api.getAnsibleRun(jobId);
            setJob(jobDetails);
        } catch (error) {
            console.error("Error fetching job details:", error);
        }
    };

    const fetchJobs = React.useCallback(async () => {
        try {
            const response = await api.getAnsibleRuns({});
            setJobs(response);
        } catch (error) {
            console.error("Error fetching jobs:", error);
        }
    }, [api, setJobs]);

    React.useEffect(() => {
        fetchJobs();
        const timer = setInterval(fetchJobs, 5000);
        return () => clearInterval(timer);
    }, [api, fetchJobs]);

    const renderAnsibleOutput = (j: Job) => {
        const output = j?.stdout || j?.stderr;
        if (!output) {
            return <div className="text-sm">No output available</div>;
        }

        const lines = output.split("\n").filter((line) => line.trim()!=="");
        return (
            <div className="font-mono text-sm whitespace-pre-wrap break-words">
                {lines.map((line, idx) => {
                    try {
                        const jsonld = JSON.parse(line);
                        return (
                            <div key={idx}>
                                {jsonld?.stdout!==undefined ? String(jsonld.stdout).trim():line}
                            </div>
                        );
                    } catch {
                        return <div key={idx}>{line}</div>;
                    }
                })}
            </div>
        );
    };

    return (
        <div className="h-screen max-h-screen overflow-hidden">
            <div className="flex h-full max-w-screen">
                {/* Sidebar */}
                <div className="w-[300px] shrink-0 border-r border-gray-300">
                    <div className="px-4 py-3">
                        <h1 className="text-lg font-semibold">Orchestra Jobs</h1>
                    </div>

                    <div className="h-[calc(100vh-56px)] overflow-y-auto border-t border-gray-200">
                        {jobs.length > 0 ? (
                            <ul className="divide-y divide-gray-200">
                                {jobs.map((j) => (
                                    <li
                                        key={j.run_id}
                                        onClick={() => handleJobClick(j.run_id)}
                                        className="cursor-pointer px-4 py-3 hover:bg-gray-200 dark:hover:bg-gray-800"
                                    >
                                        <div className="text-xs">{j.project_path}</div>
                                        <div className="mb-1 flex items-center gap-1 font-medium">
                                            <AppIcon icon={"book"} className="h-4 w-4" />
                                            <span className="text-sm">{j.playbook.replace("playbooks/", "")}</span>
                                        </div>
                                        <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                                            <AppIcon icon={"clock"} className="h-4 w-4" />
                                            <span>{formatDistanceToNow(j.created_at * 1000)} ago</span>
                                        </div>
                                        {/*<div className="mt-1">
                                            <JobStatus status={j.status} />
                                        </div>*/}
                                        {j?.stats && <div className={"mb-1"}>
                                            <AnsibleRunnerStats stats={j.stats} />
                                        </div>}
                                    </li>
                                ))}
                            </ul>
                        ):(
                            <p className="p-4 text-sm text-muted-foreground">No jobs found.</p>
                        )}
                    </div>
                </div>

                {/* Main content */}
                <div className="flex-1 overflow-y-auto p-4">
                    {job ? (
                        <div className="space-y-4">

                            <h4 className="text-base font-semibold">Stdout</h4>
                            <div className="rounded-lg border border-gray-200 p-2">
                                {renderAnsibleOutput(job)}
                            </div>

                            <div>
                                {jobEventSourceUrl && <EventSourceReader url={jobEventSourceUrl} />}
                            </div>

                            <h4 className="text-base font-semibold">Events</h4>
                            {job?.events && job.events.length > 0 ? (
                                <div className="rounded-lg border border-gray-200 bg-white">
                                    {job.events.map((event, idx) => (
                                        <JobEvent key={idx} event={event} />
                                    ))}
                                </div>
                            ):(
                                <p className="text-sm">No events found.</p>
                            )}

                            <div className="pt-2">
                                <h4 className="text-base font-semibold">Raw Job</h4>
                                <pre
                                    className="mt-2 max-h-[50vh] overflow-auto rounded-md bg-gray-50 p-3 text-xs text-gray-800">
                  {JSON.stringify(job, null, 2)}
                </pre>
                            </div>
                        </div>
                    ):(
                        <div className="p-8 text-sm text-gray-500">Select a job to view details.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OrchestraJobsPage;
