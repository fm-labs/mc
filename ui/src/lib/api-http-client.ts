import axios from "axios";
import { toast } from "react-toastify";


export const buildApiHttpClient = (baseURL: string) => {

    const http = axios.create({
        baseURL: baseURL,
        // `withCredentials` indicates whether or not cross-site Access-Control requests
        // should be made using credentials
        withCredentials: false,
        // `xsrfCookieName` is the name of the cookie to use as a value for xsrf token
        xsrfCookieName: "csrftoken",
        // `xsrfHeaderName` is the name of the http header that carries the xsrf token value
        xsrfHeaderName: "X-CSRFToken",
        // default timeout is 30 seconds
        timeout: 30000,
        // default headers
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    });


    // add a request interceptor that adds the Authorization header to each request
    // the token is stored in localStorage
    http.interceptors.request.use(
        (config) => {
            const token = localStorage.getItem("authToken");
            if (token) {
                config.headers["Authorization"] = `Bearer ${token}`;
            }
            return config;
        },
        (error) => {
            return Promise.reject(error);
        },
    );

    // add a response interceptor that handles 401 errors
    http.interceptors.response.use(
        (response) => {
            return response;
        },
        (error) => {
            if (error.response && error.response.status===401) {
                console.warn("Unauthorized! Redirecting to login...");
                toast.error("Session expired. Please log in again.");
                localStorage.removeItem("authToken");
                //window.location.href = "/auth/login";

                // get the current path and add it as a redirect parameter
                const currentPath = window.location.pathname;
                const searchParams = new URLSearchParams(/*window.location.search*/);
                searchParams.set("expired", "1");
                if (currentPath !== "/auth/login") {
                    searchParams.set("redirect", currentPath);
                }
                const redirectUrl = `/auth/login?${searchParams.toString()}`;

                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000)

            }
            return Promise.reject(error);
        },
    );

    return http;
}

