import validator from "@rjsf/validator-ajv8";
import Form from "@rjsf/shadcn";
import { Button } from "@/components/ui/button.tsx";

const jsonSchema = {
    title: "Quick Create",
    type: "object",
    properties: {
        name: { type: "string", title: "Name" },
        description: { type: "string", title: "Description" },
        template: { type: "string", title: "Template", enum: [
            "wordpress", "drupal", "joomla", "laravel", "django", "flask", "express", "react", "vue", "angular"
        ] },
    },
    required: ["name"],
}

const QuickCreateForm = () => {
    return (
        <div className="p-4">
            <p className="mt-2 text-sm text-gray-500">Quickly create a new app from a template</p>
            <Form schema={jsonSchema} validator={validator}>
                <div className="py-2">
                    <Button type="submit">Submit</Button>
                </div>
            </Form>
        </div>
    );
};

export default QuickCreateForm;
