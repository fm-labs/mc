import React from "react";
import { getIconByName } from "@/components/app-icons-map.tsx";


interface AppIconProps extends React.HTMLProps<any> {
    icon: string | React.ReactNode | React.FC, size?: number
}

const AppIcon = ({icon, size, ...props}: AppIconProps) => {
    let Icon;
    if (!icon) {
        return null;
    }
    if (typeof icon === "string") {
        Icon = getIconByName(icon)
    } else {
        Icon = icon
    }
    if (React.isValidElement(Icon)) {
        return Icon
    }
    size = size || 16;
    return <Icon height={size} width={size} {...props} />
};

export default AppIcon;
