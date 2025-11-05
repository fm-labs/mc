import { Outlet } from "react-router";

const AuthLayout = () => {
    return (
        <div id={"auth-layout"}>
            <Outlet />
        </div>
    );
};

export default AuthLayout;
