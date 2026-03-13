import React from "react";
import { useApi } from "@/context/api-context.tsx";
import { ForbiddenError } from "@/features/errors/forbidden.tsx";
import DevOnly from "@/components/dev-only.tsx";
import { Button } from "@/components/ui/button.tsx";
import { useAuth } from "@/context/auth-context.tsx";
import { isJwtExpired } from "@/utils/jwtutil.ts";

const GithubLoginPage = () => {

    const {api} = useApi()
    const { setAuthToken, authToken } = useAuth()
    const queryParams = new URLSearchParams(window.location.search);
    const code = queryParams.get("code");
    const state = queryParams.get("state");
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    const loginWithGitHubCode = async () => {
        try {
            setLoading(true);
            const response = await api.post('/api/auth/login/github', { code, state });
            console.log("GITHUB_LOGIN_RESPONSE", response);
            const accessToken = response?.access_token;
            if (accessToken) {
                console.log("GitHub login successful, setting auth token.", accessToken);
                if (isJwtExpired(accessToken)) {
                    setError("Received JWT token is expired.");
                } else {
                    setAuthToken(accessToken);
                }
            }
        } catch (error) {
            console.error("Error during GitHub login:", error);
            setError("Failed to login with GitHub. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    // React.useEffect(() => {
    //     if (code && state) {
    //         loginWithGitHubCode();
    //     }
    // }, [code, state]);

    if (!code && !state) {
        return <ForbiddenError />
    }


    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-svh p-6 md:p-10">
                <h2 className="text-red-600 mb-4">Error</h2>
                <p>{error}</p>
            </div>
        );
    }

    return (
        <div className={"flex flex-col items-center justify-center min-h-svh p-6 md:p-10"}>

            <Button onClick={loginWithGitHubCode}>
                Login with GitHub Code
            </Button>

            {authToken ? (
                <p className="mt-4 text-green-600">Logged in successfully!
                <a href={"/dashboard"} className={"underline ml-2"}>Go to Dashboard</a>
                </p>
            ) : (
                <p className="mt-4">Not logged in yet.</p>
            )}

            <DevOnly>
                <div className={"mt-8 p-4"}>
                    <hr />
                    <h2>Query Params</h2>
                    <ul>
                        {Array.from(queryParams.entries()).map(([key, value]) => (
                            <li key={key}>
                                {key}: {value}
                            </li>
                        ))}
                    </ul>
                </div>
            </DevOnly>
        </div>
    );
};

export default GithubLoginPage;
