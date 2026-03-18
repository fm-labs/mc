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

    const readerRef = React.useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
    const abortControllerRef = React.useRef<AbortController | null>(null);

    const fetchEventStream = React.useCallback(async () => {
        const controller = new AbortController();
        abortControllerRef.current = controller;

        // using fetch API to read a stream of JSON-LD events from the server
        // a line is delimited by \n and each line is a JSON-LD event
        console.log("Connecting to event stream at URL:", url);
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Accept": "application/json",
                ...headers
            },
            signal: controller.signal
        }).catch(error => {
            console.error("Error connecting to event stream:", error);
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
        //const reader = response.body.getReader();
        readerRef.current = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        const readStream = () => {
            if (!readerRef.current) {
                appendLog("No reader available for event stream.");
                setEnableStreaming(false);
                return;
            }
            readerRef.current.read().then(({ done, value }) => {
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
                console.log("Error reading event stream:", error);
                appendLog(`Error reading event stream: ${error.message}`);
                setEnableStreaming(false);
                //props.onError?.(error);
            });
        };
        console.log("Connected to event stream, starting to read...");
        readStream();
    }, [url, headers]);


    const clearLog = React.useCallback(() => {
        if (logRef.current) {
            logRef.current.innerHTML = "";
        }
    }, []);

    const appendLog = React.useCallback((message: string) => {
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
    }, [props.logFormatter]);

    const findInLog = React.useCallback((text: string, lastIndex: number) => {
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
    }, []);

    const stopStreaming = React.useCallback(() => {
        console.log("Stopping event stream...");
        setEnableStreaming(false);

        if (readerRef.current) {
            readerRef.current.cancel().catch((error) => {
                console.error("Error cancelling reader:", error);
            });
            readerRef.current = null;
        }

        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
    }, []);

    React.useEffect(() => {
        if (findText === "") return;
        const index = findInLog(findText, 0);
        let lastIndex = index !== undefined ? index : 0;
        // scroll to first found entry
        if (logRef.current && logRef.current.children[lastIndex - 1]) {
            const entry = logRef.current.children[lastIndex - 1] as HTMLDivElement;
            entry.scrollIntoView({behavior: "smooth", block: "center"});
        }
    }, [findText]);

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
        } else {
            stopStreaming();
        }
    }, [enableStreaming]);

    React.useEffect(() => {
        setEnableStreaming(!!url);
        bytesReceivedRef.current = 0;

        return () => {
            stopStreaming();
        };
    }, [url, stopStreaming]);

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
