import * as React from "react";
import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";

import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetClose,
    SheetContent,
    SheetDescription,
    SheetFooter,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";

type FormDrawerProps = {
    open: boolean
    onOpenChange?: (open: boolean) => void
    onSubmit: (values: any) => void
    onChange?: (values: any) => void
    schema: any,
    uiSchema?: any,
    title?: string,
    description?: string,
    initialValues?: any
}

export function FormDrawer({
                               open,
                               onOpenChange,
                               onSubmit,
                               onChange,
                               schema,
                               uiSchema,
                               title,
                               description,
                               initialValues,
                           }: FormDrawerProps) {

    const [formData, setFormData] = React.useState<any>(initialValues || {});

    const handleFormChange = (data: any) => {
        setFormData(data.formData);
        if (onChange) {
            onChange(data);
        }
    };

    const handleFormSubmit = (data: any) => {
        // handle form submission
        console.log("Form submitted:", data.formData);
        if (onSubmit) {
            onSubmit(data.formData);
        }
    };

    const handleOpenChange = (isOpen: boolean) => {
        if (onOpenChange) {
            onOpenChange(isOpen);
        }
    }

    const handleClose = () => {
        if (onOpenChange) {
            onOpenChange(false);
        }
    };

    return (
        <Sheet
            open={open}
            onOpenChange={handleOpenChange}
        >
            <SheetContent className="flex flex-col">
                <SheetHeader className="text-start">
                    <SheetTitle>{title}</SheetTitle>
                    <SheetDescription>
                        {description}
                    </SheetDescription>
                </SheetHeader>
                <div className={"px-4"}>
                    <Form
                        id="repos-form"
                        schema={schema}
                        uiSchema={uiSchema}
                        formData={formData}
                        onSubmit={handleFormSubmit}
                        onChange={handleFormChange}
                        validator={validator}
                        showErrorList={"top"}
                    >
                        {/*<div className="mt-4 flex justify-end">
                            <Button type="submit">Submit</Button>
                        </div>*/}
                        {' '}
                    </Form>
                </div>
                {formData && <div className="flex-1 p-2 text-xs">
                    <hr />
                    Form Data:
                    <pre
                        className="max-h-48 overflow-auto">{JSON.stringify(formData, null, 2)}</pre>
                </div>}
                <SheetFooter className="gap-2">
                    <SheetClose asChild>
                        <Button variant="outline" onClick={handleClose}>Close</Button>
                    </SheetClose>
                    <Button form="repos-form" type="submit">
                        Submit
                    </Button>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
