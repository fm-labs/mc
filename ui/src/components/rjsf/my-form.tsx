import { FormEvent } from "react";
import { Form } from "@rjsf/shadcn";
import validator from "@rjsf/validator-ajv8";
import { FormProps } from "@rjsf/core";
import { toast } from "sonner";

interface MyFormProps extends Omit<FormProps, 'validator'> {
    label?: string;
}


const MyForm = ({ onChange, onSubmit, ...props }: MyFormProps) => {

    const handleSubmit = (data: any, event: FormEvent) => {
        console.log("Form submitted with data:", data.formData);
        // Here you would typically send the data to your backend API
        event.preventDefault();
        event.stopPropagation();

        if (onSubmit) {
            return onSubmit(data, event)
        }

        toast.info(<div className={"text-sm"}>
            <h3 className={"font-bold mb-2"}>Submitted Data:</h3>
            {/*<ReactJson src={data.formData}
                       displayDataTypes={false}
                       displayObjectSize={false}
                       collapseStringsAfterLength={32}  />*/}
            <pre>{JSON.stringify(data.formData, null, 2)}</pre>
        </div>);
    };

    const handleChange = (data: any) => {
        console.log("Form data changed:", data.formData);
    };

    const handleErrors = ((errors: any) => {
        console.log(errors);
    });

    return (
        <>
            <Form
                validator={validator}
                onChange={handleChange}
                onSubmit={handleSubmit}
                onError={handleErrors}
                showErrorList={"top"}
                //id={formId}
                //schema={{}}
                //uiSchema={finalUISchema}
                //formData={values}
                noValidate={true}
                {...props}
            >{props?.children}</Form>
            {/*<Button onClick={handleSubmitClick}>Save</Button>*/}
        </>
    );
};

export default MyForm;
