import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu.tsx";
import { Button } from "@/components/ui/button.tsx";
import { IconDotsVertical } from "@tabler/icons-react";
import { PropsWithChildren } from "react";

interface DropdownMenuDotsProps extends PropsWithChildren {
    actions?: {
        label: string;
        onClick?: () => void;
        variant?: "default" | "destructive";
    }[];

}

const DropdownMenuDots = (props: DropdownMenuDotsProps) => {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    className="data-[state=open]:bg-muted text-muted-foreground flex size-8"
                    size="icon"
                >
                    <IconDotsVertical />
                    <span className="sr-only">Open menu</span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
                {props.children ? props.children :
                props.actions?.map((action, idx) => {
                    if (action.label === "separator") {
                        return <DropdownMenuSeparator key={`sep-${idx}`} />;
                    }

                    return (
                        <DropdownMenuItem
                            key={action.label}
                            onClick={action?.onClick}
                            variant={action.variant || "default"}
                        >
                            {action.label}
                        </DropdownMenuItem>
                    )
                })}
            </DropdownMenuContent>
        </DropdownMenu>
    );
};

export default DropdownMenuDots;
