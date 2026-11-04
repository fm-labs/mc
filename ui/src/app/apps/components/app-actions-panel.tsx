import React from "react";
import { toast } from "sonner";
import { IconPlayerPlay, IconPlayerStop, IconRefresh, IconSquareX, IconX } from "@tabler/icons-react";
import { useApi } from "@/context/api-context.tsx";
import SectionCard from "@/components/section-card.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { AppAction } from "@/features/apps/apps.types.ts";
import { StreamEvent } from "@/features/stream/stream.types.ts";

const ACTIONS: { action: AppAction; label: string; icon: React.ReactNode; variant?: "default" | "secondary" | "outline" | "destructive" }[] = [
    { action: "up", label: "Up", icon: <IconPlayerPlay size={16} /> },
    { action: "restart", label: "Restart", icon: <IconRefresh size={16} />, variant: "secondary" },
    { action: "stop", label: "Stop", icon: <IconPlayerStop size={16} />, variant: "secondary" },
    { action: "down", label: "Down", icon: <IconSquareX size={16} />, variant: "destructive" },
];

/**
 * Run docker compose actions for an app and show the live output.
 */
const AppActionsPanel = ({ appId, disabledReason }: { appId: string; disabledReason?: string | null }) => {
    const { api } = useApi();
    const [running, setRunning] = React.useState<AppAction | null>(null);
    const [lastAction, setLastAction] = React.useState<AppAction | null>(null);
    const [lines, setLines] = React.useState<string[] | null>(null);
    const [rc, setRc] = React.useState<number | null>(null);
    const abortRef = React.useRef<AbortController | null>(null);
    const logRef = React.useRef<HTMLPreElement | null>(null);

    React.useEffect(() => {
        logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
    }, [lines]);

    // stop streaming when leaving the page
    React.useEffect(() => () => abortRef.current?.abort(), []);

    const runAction = async (action: AppAction) => {
        const controller = new AbortController();
        abortRef.current = controller;
        setRunning(action);
        setLastAction(action);
        setLines([]);
        setRc(null);
        try {
            await api.streamAppAction(appId, action, (ev: StreamEvent) => {
                if (ev.event === "RC") {
                    setRc(Number(ev.data));
                    return;
                }
                const line = ev.event === "STDOUT" ? ev.data : `[${ev.event}] ${ev.data}`;
                setLines((prev) => [...(prev || []), line]);
            }, controller.signal);
        } catch (error: any) {
            if (error?.name !== "AbortError") {
                toast.error(error?.message || `compose ${action} failed`);
            }
        } finally {
            abortRef.current = null;
            setRunning(null);
        }
    };

    const header = (
        <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
                <h2 className="text-lg font-semibold">Run</h2>
                <p className="text-sm text-muted-foreground">
                    {disabledReason || "Run docker compose for this app. Output streams below."}
                </p>
            </div>
            <div className="flex flex-wrap gap-2">
                {ACTIONS.map(({ action, label, icon, variant }) => (
                    <Button
                        key={action}
                        variant={variant ?? "default"}
                        disabled={!!running || !!disabledReason}
                        onClick={() => runAction(action)}
                    >
                        {icon} {running === action ? `${label}...` : label}
                    </Button>
                ))}
                {running && (
                    <Button variant="outline" onClick={() => abortRef.current?.abort()}>
                        <IconX size={16} /> Stop streaming
                    </Button>
                )}
            </div>
        </div>
    );

    return (
        <SectionCard headerEl={header}>
            {lines !== null && (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-sm">
                        <span className="font-mono text-muted-foreground">docker compose {lastAction}</span>
                        {running && <Badge variant="outline" className="animate-pulse">streaming</Badge>}
                        {rc !== null && <Badge variant={rc === 0 ? "default" : "destructive"}>exit {rc}</Badge>}
                    </div>
                    <pre
                        ref={logRef}
                        className="rounded-md bg-muted px-3 py-2 font-mono text-xs whitespace-pre-wrap break-all max-h-96 overflow-auto"
                    >
                        {lines.join("\n") || "Waiting for output..."}
                    </pre>
                </div>
            )}
        </SectionCard>
    );
};

export default AppActionsPanel;
