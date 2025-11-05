import React from "react"
import { LoginForm } from "@/app/auth/components/login-form.tsx"
import { LoginData, useAuth } from "@/context/auth-context.tsx";
import { toast } from "react-toastify";
import { Link, useNavigate } from "react-router";

const REDIRECT_URL = '/dashboard';

export default function LoginPage() {
    const auth = useAuth()
    const navigate = useNavigate();

    const searchParams = new URLSearchParams(window.location.search);
    const redirect = searchParams.get("redirect");
    const expired = searchParams.get("expired");

    //const [isSubmitting, setIsSubmitting] = React.useState(false);
    const redirectUrl = redirect ? decodeURIComponent(redirect) : REDIRECT_URL;
    const isSessionExpired = expired === '1';

    const handleLoginFormSubmit = async (loginData: LoginData) => {
        try {
            const p = auth.login(loginData)
            await toast.promise(p, {
                pending: 'Logging in...',
                success: 'Logged in successfully!',
                error: 'Login failed!'
            })
            //.then(() => {
            //    navigate(REDIRECT_URL);
            //});
        } catch (error) {
            toast.error("Error during login. Please try again.");
            console.error("Login error:", error);
            return;
        }
    }

    React.useEffect(() => {
        if (auth.isLoggedIn) {
            navigate(redirectUrl);
            //toast.info("Logged in!");
        }
    }, [auth.isLoggedIn, navigate]);

    return (
        <div className="bg-muted flex min-h-svh flex-col items-center justify-center p-6 md:p-10">
            <div className="w-full max-w-sm">
                {isSessionExpired && <div className="mb-4 rounded-md bg-yellow-50 p-4">
                    <p className="text-sm text-yellow-700">Your session has expired. Please log in again.</p>
                </div>}
                <LoginForm onSubmit={handleLoginFormSubmit} />
                <div className="text-center mt-4">
                    <Link to={"/"} className="text-sm text-primary hover:underline inline-block">
                        Go back
                    </Link>
                </div>
            </div>
        </div>
    )
}
