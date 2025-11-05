import React from "react";
import { Badge } from "@/components/ui/badge.tsx";

interface EventSourceReaderProps {
    url: string;
    logFormatter?: (message: string) => string;
    //onMessage: (data: any) => void;
    //onError: (error: any) => void;
    //onComplete: () => void;
    //onStop: () => void;
}

export const EventSourceReader = ({ url, ...props }: EventSourceReaderProps) => {
    const esRef = React.useRef<EventSource | null>(null);
    const logRef = React.useRef<HTMLDivElement | null>(null);
    const bytesReceivedRef = React.useRef<number>(0);
    const statsContainerRef = React.useRef<HTMLDivElement | null>(null);

    const [enableStreaming, setEnableStreaming] = React.useState<boolean>(false);

    const clearLog = () => {
        if (logRef.current) {
            logRef.current.innerHTML = "";
        }
    };

    const appendLog = (message: string) => {
        if (logRef.current) {
            let _message = message;
            if (props.logFormatter) {
                _message = props.logFormatter(message);
            }

            const newLogEntry = document.createElement("div");
            newLogEntry.classList.add("hover:bg-lime-100", "dark:hover:bg-lime-900");
            newLogEntry.textContent = _message;
            logRef.current.appendChild(newLogEntry);
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    };

    // const handleContainerClick = (e: React.MouseEvent<HTMLDivElement>) => {
    //     const container = e.currentTarget;
    //     const target = e.target as HTMLElement | null;
    //
    //     if (!target) return;
    //
    //     // Find the nearest direct child <div> of the container
    //     const child = target.closest(':scope > div') as HTMLDivElement | null;
    //     if (!child || child.parentElement !== container) return;
    //
    //     // 👉 handle click on that child div here
    //     console.log('Clicked child div:', child.textContent);
    // };

    React.useEffect(() => {
        if (esRef.current) {
            esRef.current.close();
            esRef.current = null;
        }
        if (enableStreaming) {
            bytesReceivedRef.current = 0;
            clearLog();

            console.log("Starting EventSource for:", url);
            const eventSource = new EventSource(url);
            eventSource.onmessage = (event) => {
                console.log("Event received:", event);
                bytesReceivedRef.current += event.data.length;
                if (statsContainerRef.current) {
                    statsContainerRef.current.textContent = `Received ${bytesReceivedRef.current} bytes so far.`;
                }
                appendLog(event.data);

                try {
                    const data = JSON.parse(event.data);

                    if (data?.type==="complete") {
                        console.log("Stream complete, closing EventSource.");
                        eventSource.close();
                        esRef.current = null;
                        setEnableStreaming(false);
                    }
                } catch (e) {
                    console.error("Error parsing JSON:", e);
                    return;
                }

            };

            eventSource.onerror = (error) => {
                console.error("EventSource failed:", error);
                appendLog("Error occurred. Check console for details.");

                if (eventSource.readyState !== EventSource.CLOSED) {
                    console.log("Closing EventSource due to error.");
                    eventSource.close();
                }
                esRef.current = null;
                setEnableStreaming(false);
            };
            esRef.current = eventSource;
        }
        return () => {
            if (esRef.current) {
                if (esRef.current.readyState !== EventSource.CLOSED) {
                    console.log("Closing EventSource on unmount.");
                    esRef.current.close();
                }
                esRef.current = null;
            }
        };
    }, [enableStreaming, url]);

    React.useEffect(() => {
        setEnableStreaming(true);
        if (bytesReceivedRef.current) {
            bytesReceivedRef.current = 0;
        }
    }, [url])

    const renderStatus = () => {
        if (enableStreaming) {
            if (bytesReceivedRef.current == 0) {
                return <Badge variant={"outline"} className={"border-green-200"}>Connecting to event stream...</Badge>
            } else {
                return <Badge variant="default" className="cursor-pointer bg-green-500"
                              title={"Click badge to stop."}
                              onClick={() => setEnableStreaming(false)}>Streaming ...</Badge>
            }
        } else {
            return <Badge variant={"outline"} className={"border-red-500"}>Stream closed</Badge>
        }
    }

    return (
        <div>
            {renderStatus()}
            <span ref={statsContainerRef} className={"ml-1 text-secondary-foreground text-xs"}></span>
            <div ref={logRef}
                 //onClick={handleContainerClick}
                 className="mt-1 h-96 w-full overflow-y-scroll overflow-x-hidden border p-1 text-sm font-mono whitespace-pre-wrap break-all [overflow-wrap:anywhere]">
                <div>Event log will appear here...</div>
            </div>
        </div>
    );
};
