import React from "react";
import {Badge} from "@/components/ui/badge.tsx";
import DevOnly from "@/components/dev-only.tsx";

interface EventStreamReaderProps {
    url: string;
    headers?: Record<string, string>;
    logFormatter?: (message: string) => string;
    //onMessage: (data: any) => void;
    //onError: (error: any) => void;
    //onComplete: () => void;
    //onStop: () => void;
}

export const EventStreamReader = ({url, headers, ...props}: EventStreamReaderProps) => {
    const logRef = React.useRef<HTMLDivElement | null>(null);
    const bytesReceivedRef = React.useRef<number>(0);
    const statsContainerRef = React.useRef<HTMLDivElement | null>(null);

    const [enableStreaming, setEnableStreaming] = React.useState<boolean>(false);
    const [findText, setFindText] = React.useState<string>("");

    const fetchEventStream = async () => {
        // using fetch API to read a stream of JSON-LD events from the server
        // a line is delimited by \n and each line is a JSON-LD event
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Accept": "application/json",
                ...headers
            }
        }).catch(error => {
            appendLog(`Error connecting to event stream: ${error.message}`);
            setEnableStreaming(false);
            //props.onError?.(error);
        });

        if (!response || !response.ok || !response.body) {
            const errorMsg = `Failed to connect to event stream: ${response ? response.statusText : "No response"}`;
            appendLog(errorMsg);
            setEnableStreaming(false);
            throw new Error("No response body");
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        const readStream = () => {
            reader.read().then(({ done, value }) => {
                if (done) {
                    appendLog("Event stream closed by server.");
                    setEnableStreaming(false);
                    return;
                }
                bytesReceivedRef.current += value.length;
                if (statsContainerRef.current) {
                    statsContainerRef.current.textContent = `Bytes received: ${bytesReceivedRef.current}`;
                }
                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split("\n");
                buffer = lines.pop() || ""; // Keep the last partial line in the buffer
                lines.forEach(line => {
                    if (line.trim()) {
                        appendLog(line.trim());
                        //props.onMessage?.(line.trim());
                    }
                });
                readStream();
            }).catch(error => {
                appendLog(`Error reading event stream: ${error.message}`);
                setEnableStreaming(false);
                //props.onError?.(error);
            });
        };
        readStream();
    }


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

    const findInLog = (text: string, lastIndex: number) => {
        if (logRef.current) {
            const logEntries = logRef.current.children;
            for (let i = lastIndex; i < logEntries.length; i++) {
                const entry = logEntries[i] as HTMLDivElement;
                if (entry.textContent && entry.textContent.includes(text)) {
                    entry.style.backgroundColor = "rgba(255, 255, 0, 0.5)"; // Highlight found entry
                    return i + 1; // Return next index to continue search
                }
            }
        }
    }

    React.useEffect(() => {
        if (findText === "") return;
        const index = findInLog(findText, 0);
        let lastIndex = index !== undefined ? index : 0;
        // scroll to first found entry
        if (logRef.current && logRef.current.children[lastIndex - 1]) {
            const entry = logRef.current.children[lastIndex - 1] as HTMLDivElement;
            entry.scrollIntoView({behavior: "smooth", block: "center"});
        }
    })

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
        if (enableStreaming) {
            clearLog();
            fetchEventStream();
        }
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
                 className="mt-1 h-64 w-full overflow-y-scroll overflow-x-hidden border p-1 text-sm font-mono whitespace-pre-wrap break-all [overflow-wrap:anywhere]">
                <div>Event log will appear here...</div>
            </div>
            <DevOnly>
                <input type={"text"}
                       value={findText}
                       placeholder={"Enter search query ..."}
                       onChange={(e) => setFindText(e.target.value)}/>
            </DevOnly>
        </div>
    );
};
