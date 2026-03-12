import React from 'react';
import MyForm from "@/components/rjsf/my-form.tsx";
import {RJSFSchema} from "@rjsf/utils";

const creditsBuySchema: RJSFSchema = {
    type: "object",
    properties: {
        "currency_amount": {
            type: "number",
            title: "Currency Amount",
            default: 10,
        },
        "currency": {
            type: "string",
            title: "Currency",
            enum: ["USD", "EUR", "GBP"],
            default: "USD",
        },
        "payment_method": {
            type: "string",
            title: "Payment Method",
            enum: ["credit_card", "paypal", "bank_transfer"],
            default: "credit_card",
        },
    },
    required: ["currency_amount", "currency", "payment_method"],
}


export const CreditsForm = () => {
    return (
        <div>
            <h1>Credits</h1>
            <p>This is the Credits Form component.</p>


            <MyForm
                schema={creditsBuySchema}
                onSubmit={(data) => {
                    console.log('Form submitted with data:', data);
                }}
            />
        </div>
    );
};

export default CreditsForm;