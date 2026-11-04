import { isRouteErrorResponse, useNavigate, useRouteError } from "react-router";
import { Button } from "@/components/ui/button.tsx";

type ErrorSummary = {
    status?: number
    message: string
    stack?: string
}

// Router responses (thrown Response / 404), axios errors from loaders and API calls, and plain errors.
const summarize = (error: unknown): ErrorSummary => {
    if (isRouteErrorResponse(error)) {
        const detail = typeof error.data === "string" ? error.data : error.data?.detail || error.data?.message;
        return { status: error.status, message: detail || error.statusText || "Request failed" };
    }
    const err = error as any;
    if (err?.isAxiosError) {
        const detail = err.response?.data?.detail;
        return {
            status: err.response?.status,
            message: (typeof detail === "string" ? detail : null) || err.message || "Request failed",
        };
    }
    if (error instanceof Error) {
        return { message: error.message || "Unexpected error", stack: error.stack };
    }
    return { message: typeof error === "string" ? error : "Unexpected error" };
};

// Short titles for common statuses, in the style of the other error pages.
const STATUS_TITLES: Record<number, string> = {
    400: "Bad Request",
    401: "Unauthorized Access",
    403: "Access Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
};

/**
 * Error boundary of the root route. Catches errors thrown while rendering any route and errors
 * from loaders, and replaces the whole page. Same layout as the other pages in features/errors.
 */
export function RouteError() {
    const error = useRouteError();
    const navigate = useNavigate();
    const { status, message, stack } = summarize(error);

    return (
        <div className='h-svh'>
            <div className='m-auto flex h-full w-full max-w-2xl flex-col items-center justify-center gap-2 px-4'>
                <h1 className='text-[7rem] leading-tight font-bold'>{status || 500}</h1>
                <span className='font-medium'>
                    {(status && STATUS_TITLES[status]) || "Oops! Something went wrong"}
                </span>
                <p className='text-muted-foreground text-center break-words'>{message}</p>
                <div className='mt-6 flex gap-4'>
                    <Button variant='outline' onClick={() => navigate(-1)}>Go Back</Button>
                    <Button variant='outline' onClick={() => window.location.reload()}>Try Again</Button>
                    <Button onClick={() => navigate('/')}>Back to Home</Button>
                </div>
                {import.meta.env.DEV && stack && (
                    <details className='mt-6 w-full text-sm text-muted-foreground'>
                        <summary className='cursor-pointer select-none text-center'>Show details</summary>
                        <pre className='mt-2 max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap'>
                            {stack}
                        </pre>
                    </details>
                )}
            </div>
        </div>
    );
}
