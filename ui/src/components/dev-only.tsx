import { PropsWithChildren } from "react";

const DevOnly = ({children}: PropsWithChildren<any>) => {
    if (import.meta.env.PROD) {
        return null;
    }

    if (process.env.NODE_ENV !== "development") {
        return null;
    }

    return children
};

export default DevOnly;
