import { Outlet } from "react-router";

const Root = () => {
    return (
        <div id={"app-root"}>
            <Outlet />
        </div>
    );
};

export default Root;
