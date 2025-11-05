import { AppProvider } from "@/context/app-context.tsx";
import { ThemeProvider } from "@/context/theme-provider.tsx";
import { ToastContainer } from "react-toastify";
import { ApiProvider } from "@/context/api-context.tsx";
import { AuthProvider } from "@/context/auth-context.tsx";
import { SearchProvider } from "@/context/search-provider.tsx";
import { Toaster } from "@/components/ui/sonner.tsx";
import ErrorBoundary from "@/components/error-boundary.tsx";
import ApiRouter from "@/api-router.tsx";

const appConfig = {};

function App() {

    return (
        <AppProvider config={appConfig}>
            <ThemeProvider defaultTheme="dark" storageKey="app-ui-theme">
                <SearchProvider>
                    <ErrorBoundary>
                        <ApiProvider>
                            <AuthProvider>
                                <ApiRouter />
                            </AuthProvider>
                        </ApiProvider>
                    </ErrorBoundary>
                </SearchProvider>
                <Toaster />
                <ToastContainer
                    position="top-right"
                    autoClose={5000}
                    hideProgressBar={false}
                    newestOnTop={false}
                    closeOnClick
                    rtl={false}
                    pauseOnFocusLoss
                    draggable
                    pauseOnHover
                    theme="dark"
                />
                {/*<MasterPanel />*/}
            </ThemeProvider>
        </AppProvider>
    );
}

export default App;
