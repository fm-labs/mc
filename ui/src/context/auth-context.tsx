import React from "react";
import { useApi } from "@/context/api-context.tsx";
import { isJwtExpired } from "@/utils/jwtutil.ts";

export type LoginData = {
    username: string
    password: string
}

type UserData = {
    username: string
    email?: string
}

type AuthContextType = {
    authToken: string | null;
    setAuthToken: (token: string | null) => void;
    login: (loginData: LoginData) => Promise<void>;
    logout: () => Promise<void>;
    isLoggedIn: boolean;
    user: UserData | null;
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

const AUTH_LOCAL_STORAGE_KEY = "authToken";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { api } = useApi()

    const [user, setUser] = React.useState<UserData | null>(null);
    const [authToken, _setAuthToken] = React.useState<string | null>(localStorage.getItem('authToken'));

    const setAuthToken = (token: string | null) => {
        _setAuthToken(token);
        if (token) {
            localStorage.setItem(AUTH_LOCAL_STORAGE_KEY, token);
        } else {
            localStorage.removeItem(AUTH_LOCAL_STORAGE_KEY);
        }
    }

    const resetAuth = () => {
        setAuthToken(null);
        setUser(null);
    }

    const login = async (loginData: LoginData) => {
        console.log("login", loginData.username, "**********");
        //const response = await api.authLogin(loginData)
        const formData = new FormData();
        formData.append("username", loginData.username);
        formData.append("password", loginData.password);

        const response = await api.authLoginFormData(formData).catch((error: any) => {
            console.error("Login error:", error);
            resetAuth();
            throw error;
        })
        if (!response) {
            console.error("Login failed: No response");
            resetAuth();
            throw new Error("Login failed");
        }

        const { access_token, user } = response;
        console.log("Login successful, access_token:", access_token, "user:", user);
        setAuthToken(access_token);
        //setUser(user);
        return response;
    }

    const logout = async () => {
        await api.authLogout()
            .then(() => console.info("Logged out"))
            .catch((error: any) => {
                console.warn("Logout error:", error);
            })
            .finally(resetAuth);
    }

    const isLoggedIn: boolean = React.useMemo(() => {
        return !!authToken && !isJwtExpired(authToken);
    }, [authToken]);


    React.useEffect(() => {
        if (authToken) {
            if (isJwtExpired(authToken)) {
                console.warn("Auth token expired, resetting..");
                //logout();
                //resetAuth();
            } else {
                console.log("Auth token valid");
            }
        }
    }, [authToken]);

    const fetchAndSetUser = React.useCallback(() => {
        if (!authToken) {
            return;
        }
        // fetch user data
        api.get("/api/auth/user").then((res: any) => {
            console.log("Fetched user data:", res);
            setUser(res);
        }).catch((error: any) => {
            console.error("Failed to fetch user data:", error);
        })
    }, [authToken, api, setUser]);

    React.useEffect(() => {
        if (!isLoggedIn) {
            if (authToken || user) {
                console.warn("User is not logged in but auth data exists, resetting..");
                resetAuth();
            }
            return;
        }
        fetchAndSetUser();

        // auto-refresh user data every 5 minutes
        // this will trigger logout if the token is expired
        const interval = setInterval(fetchAndSetUser, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, [isLoggedIn])

    return (
        <AuthContext.Provider value={{ authToken, setAuthToken, login, logout, isLoggedIn, user }}>
            {children}
        </AuthContext.Provider>
    );
}


export const useAuth = () => {
    const context = React.useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
