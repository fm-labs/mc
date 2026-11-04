// Streaming endpoints (format=json) emit one event per line, see src/mc/server/stream_helper.py
export type StreamEvent = {
    event: "STDOUT" | "RC" | "ERROR" | string;
    data: string;
};
