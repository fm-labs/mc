import React from "react";
import AuthBoundary from "@/components/auth-boundary.tsx";
import { Outlet } from "react-router";

const AuthenticatedRoute = () => {
    return (
        <AuthBoundary>
            <Outlet />
        </AuthBoundary>
    );
};

export default AuthenticatedRoute;
