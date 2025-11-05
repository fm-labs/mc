import { PropsWithChildren } from "react";
import { useAuth } from "@/context/auth-context.tsx";
import { UnauthorisedError } from "@/features/errors/unauthorized-error.tsx";

const AuthBoundary = (props: PropsWithChildren<any>) => {
    const auth = useAuth()

    if (!auth.isLoggedIn) {
        return <UnauthorisedError />
    }

    return <>{props.children}</>;
};

export default AuthBoundary;
