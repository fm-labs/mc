import React, { PropsWithChildren } from "react";
import { createPortal } from "react-dom";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog.tsx";
import { Button } from "@/components/ui/button.tsx";
import {
    Sheet,
    SheetClose,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet.tsx";

const MyDialog = ({ children, title, description, onClose, size }: PropsWithChildren<{
    title?: string,
    description?: string,
    onClose?: () => void
    size?: string;
}>) => {
    const [showDialog, setShowDialog] = React.useState<boolean>(true);
    const [dialogSize, setDialogSize] = React.useState<string>(size || "sm");

    return (<Dialog
        open={showDialog}
        onOpenChange={(state) => {
            setShowDialog(state);
            if (!state && onClose) {
                onClose();
            }
        }}
    >
        <DialogContent className={`sm:max-w-${dialogSize} sm:w-${dialogSize} w-${dialogSize}`}>
            <DialogHeader className="text-start">
                <DialogTitle>{title}</DialogTitle>
                <DialogDescription>
                    {description}
                    <div>
                        {["md", "lg", "xl", "2xl", "4xl", "1/2", "3/4", "full"].map((size) => {
                            return (<Button key={size} size={"sm"} variant={dialogSize === size ? "default" : "outline"}
                                            className={"mr-1 mb-1"}
                                            onClick={() => setDialogSize(size)}>
                                {size}
                            </Button>);
                        })}
                    </div>
                </DialogDescription>
            </DialogHeader>
            <div>
                {children}
            </div>
            <DialogFooter>
                {/*<Button type="submit" form="user-form">
                    Save changes
                </Button>*/}
            </DialogFooter>
        </DialogContent>
    </Dialog>);
};

const MyDrawer = ({ children, title, description, onClose, size }: PropsWithChildren<{
    title?: string,
    description?: string,
    onClose?: () => void,
    size?: string;
}>) => {
    const [showDialog, setShowDialog] = React.useState<boolean>(true);
    const [drawerSize, setDrawerSize] = React.useState<string>(size || "sm");

    // React.useEffect(() => {
    //     if (drawerSize) {
    //         setShowDialog(false)
    //         setTimeout(() => setShowDialog(true), 500)
    //     }
    // }, [drawerSize])

    return (<Sheet
        open={showDialog}
        onOpenChange={(state) => {
            setShowDialog(state);
            if (!state && onClose) {
                onClose();
            }
        }}
    >
        <SheetContent className={`sm:max-w-${drawerSize} sm:w-${drawerSize} w-${drawerSize} overflow-y-scroll`}>
            <SheetHeader className="text-start">
                <SheetTitle>{title}</SheetTitle>
                <SheetDescription>
                    {description}
                    <span>
                        {["sm", "lg", "2xl", "4xl", "3/4", "full"].map((size) => {
                            return (<Button key={size} size={"sm"} variant={drawerSize === size ? "default" : "outline"}
                                            className={"mr-1 mb-1"}
                                            onClick={() => setDrawerSize(size)}>
                                {size}
                            </Button>);
                        })}
                    </span>
                </SheetDescription>
            </SheetHeader>
            <div className={"p-4"}>
                {children}
            </div>
            <SheetFooter className="gap-2">
                <SheetClose asChild>
                    <Button variant="outline">Close</Button>
                </SheetClose>
            </SheetFooter>
        </SheetContent>
    </Sheet>);
};

const useDialog = () => {

    const createDialog = ({
                              title, children, onClose, size,
                          }: {
        title?: string;
        children: React.ReactNode;
        onClose?: () => void;
        size?: string;
    }) => {

        console.log("Creating dialog with title:", title);

        const handleClose = () => {
            if (onClose) {
                onClose();
            }
        };

        return createPortal(
            <MyDialog title={title} size={size} onClose={handleClose}>
                {children}
            </MyDialog>,
            document.getElementById("modal-root") as HTMLElement,
        );
    };

    const createDrawer = ({
                              title, children, onClose, size
                          }: {
        title?: string;
        children: React.ReactNode;
        onClose?: () => void;
        size?: string;
    }) => {

        const handleClose = () => {
            if (onClose) {
                onClose();
            }
        };

        return (<MyDrawer title={title} size={size} onClose={handleClose}>
            {children}
        </MyDrawer>)

        // return createPortal(
        //     <MyDrawer title={title} onClose={handleClose}>
        //         {content}
        //     </MyDrawer>,
        //     document.getElementById("modal-root") as HTMLElement,
        // );
    };

    return { createDialog, createDrawer };
};


export default useDialog;
