import { Button } from "@/components/ui/button.tsx";
import { useApi } from "@/context/api-context.tsx";
import React from "react";
import { toast } from "sonner";
import { useNavigate } from "react-router";

const WelcomePage = () => {
    const { apiBaseUrl, setApiBaseUrl, api } = useApi();
    const navigate = useNavigate()

    const [inputValue, setInputValue] = React.useState<string>(apiBaseUrl);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        // Handle input change if needed
        setInputValue(e.target.value);
    };

    const handleConnect = () => {
        // Handle connect action if needed
        // if (inputValue && inputValue!==apiBaseUrl) {
        //     toast.info("Changing Endpoint URL...");
        //     let _url = inputValue;
        //     // ensure trailing slash is removed
        //     if (_url.endsWith("/")) {
        //         _url = inputValue.slice(0, -1);
        //     }
        //     setApiBaseUrl(_url + "/");
        // }
        toast.info("Connecting ...");
        setTimeout(async () => {
            toast.success("Endpoint URL set successfully! Connecting...");

            // Test the connection
            api.get("/api/info").then((_response: any) => {
                toast.success("Connected to server successfully!");
                //window.location.href = "/auth/login";
                navigate("/auth/login");
            }).catch((_error: any) => {
                toast.error("Failed to connect to server. Please check the URL and try again.");
            });
        }, 500);
    };


    return (
        <div className="h-svh">
            <div className="m-auto flex h-full w-full flex-col items-center justify-center gap-2">
                <h1 className="text-[5rem] leading-tight font-bold">mc</h1>
                {/*<p className={"font-medium text-muted-foreground"}>Connect to mission control console</p>*/}
                {/*<span className='font-medium'>powered by kontxt labs</span>*/}
                {/*<p className="text-muted-foreground text-center">*/}
                {/*    Server Endpoint URL:*/}
                {/*</p>*/}
                {/*<div>*/}
                {/*    <input type="text"*/}
                {/*           //placeholder={"http://localhost:1337/mc"}*/}
                {/*           value={inputValue}*/}
                {/*           onChange={handleInputChange}*/}
                {/*           className="border rounded-md px-2 py-1 w-80 text-center" />*/}
                {/*</div>*/}
                <div className="mt-4 flex gap-4">
                    {/*<Button variant="outline" asChild>
                        <Link to="/auth/login">Connect</Link>
                    </Button>*/}
                    <Button variant="outline" onClick={handleConnect}>
                        Connect
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default WelcomePage;
