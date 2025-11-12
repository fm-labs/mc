import { RJSFSchema } from "@rjsf/utils";


const schema: RJSFSchema = {
    "type": "object",
    "properties": {
        "domain": { "type": "string", "title": "Domain" },
        "type": {
            "type": "string",
            "title": "Type",
            "enum": ["A", "AAAA", "CNAME", "MX", "TXT", "SRV", "NS", "PTR"],
        },
        "value": { "type": "string", "title": "Value" },
        "ttl": { "type": "integer", "title": "TTL (seconds)", "default": 3600 },
        "priority": { "type": "integer", "title": "Priority", "default": 10 },
        "createdAt": { "type": "string", "format": "date-time", "title": "Created At" },
        "updatedAt": { "type": "string", "format": "date-time", "title": "Updated At" },
    },
    "required": ["domain", "type", "value"],
}

export default schema;
