import { RJSFSchema } from "@rjsf/utils";

export const findingSchema: RJSFSchema = {
    "type": "object",
    "properties": {
        "name": { "type": "string", "title": "Name" },
        "url": { "type": "string", "title": "URL" },
        "branch": { "type": "string", "title": "Branch" },
        "authType": {
            "type": "string",
            "title": "Authentication Type",
            "enum": ["none", "ssh", "https"],
        },
        "sshKey": { "type": "string", "title": "SSH Key" },
        "username": { "type": "string", "title": "Username" },
        "password": { "type": "string", "title": "Password" },
    },
    "required": ["name", "url"],
};
