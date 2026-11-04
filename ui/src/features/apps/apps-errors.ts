/** Readable message from an API error, including FastAPI validation error lists. */
export const apiErrorMessage = (error: any): string => {
    const detail = error?.response?.data?.detail;
    // FastAPI validation errors: [{loc: ["body", "volumes", 0, "container_path"], msg: "..."}]
    if (Array.isArray(detail)) {
        return detail.map((d: any) => {
            const loc = (d.loc || []).filter((part: any) => part !== "body").join(".");
            return loc ? `${loc}: ${d.msg}` : d.msg;
        }).join("; ");
    }
    return detail ?? error?.message ?? String(error);
};
