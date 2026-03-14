import React from 'react';
import Header from "@/components/header.tsx";
import {InventoryProvider} from "@/app/inventory/components/inventory-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import {ucFirst} from "@/utils/textutil.ts";
import {InventoryPrimaryButtons} from "@/app/inventory/components/inventory-primary-buttons.tsx";
import InventoryDataTable from "@/app/inventory/components/inventory-data-table.tsx";
import DevOnly from "@/components/dev-only.tsx";
import {Link, useLoaderData} from "react-router";
import {Button} from "@/components/ui/button.tsx";
import AppStacksGrid from "@/app/app-stacks/components/app-stacks-grid.tsx";
import Data from "@/components/data.tsx";
import {ArrowUpIcon} from "lucide-react";
import ReactJson from "@microlink/react-json-view";
import {KeyValueTable} from "@/components/key-value-table.tsx";
import InventoryItemActionButtons from "@/app/inventory/components/inventory-item-action-buttons.tsx";
import MyForm from "@/components/rjsf/my-form.tsx";
import AppStackConfig from "@/app/app-stacks/components/app-stack-config.tsx";
import AppStackStackfile from "@/app/app-stacks/components/app-stack-stackfile.tsx";

const networkConfigSchema = {
    title: "Network Configuration",
    type: "object",
    properties: {
        ipAddress: {
            type: "string",
            title: "IP Address",
        },
        subnetMask: {
            type: "string",
            title: "Subnet Mask",
        },
        gateway: {
            type: "string",
            title: "Gateway",
        },
        dnsServers: {
            type: "array",
            title: "DNS Servers",
            items: {
                type: "string",
            },
        },
    },
    required: ["ipAddress", "subnetMask", "gateway"],
}


const traefikConfigSchema = {
    title: "Traefik Configuration",
    type: "object",
    properties: {
        entryPoints: {
            type: "array",
            title: "Entry Points",
            items: {
                type: "string",
                enum: ["web", "websecure", "admin"],
            },
        },
        middlewares: {
            type: "array",
            title: "Middlewares",
            items: {
                type: "string",
            },
        },
        routers: {
            type: "array",
            title: "Routers",
            items: {
                type: "string",
            },
        },
        services: {
            type: "array",
            title: "Services",
            items: {
                type: "string",
            },
        },
    },
    required: ["entryPoints", "routers", "services"],
}


const stackNetworkConfigSchema = {
    title: "Stack Network Configuration",
    type: "object",
    properties: {
        network_enabled: {
            type: "boolean",
            title: "Networking Enabled",
            default: false,
        },
        // network_mode: {
        //     type: "string",
        //     title: "Network Mode",
        //     enum: ["gateway", "bridge", "host", "none"],
        //     default: "none",
        // },
        network_http_enabled: {
            type: "boolean",
            title: "HTTP Traffic Enabled (insecure)",
            description: "Not recommended for production use.",
            default: false,
        },
        network_https_enabled: {
            type: "boolean",
            title: "HTTPS Traffic Enabled",
            default: false,
        },
        domain_name: {
            type: "string",
            title: "Domain Name (required for HTTPS)",
        },
    }
}

const cspPolicyConfigSchema = {
    title: "CSP Policy Configuration",
    type: "object",
    properties: {
        csp_enabled: {
            type: "boolean",
            title: "Enable Content Security Policy (CSP)",
            default: false,
        },
        default_src: {
            type: "string",
            title: "default-src",
            default: "'self'",
        },
        script_src: {
            type: "string",
            title: "script-src",
            default: "'self'",
        },
        style_src: {
            type: "string",
            title: "style-src",
            default: "'self'",
        },
        img_src: {
            type: "string",
            title: "img-src",
            default: "'self' data:",
        },
        media_src: {
            type: "string",
            title: "media-src",
            default: "'self' data:",
        },
        base_uri: {
            type: "string",
            title: "base-uri",
            default: "'self'",
        },
        connect_src: {
            type: "string",
            title: "connect-src",
            default: "'self'",
        },
        font_src: {
            type: "string",
            title: "font-src",
            default: "'self'",
        },
        object_src: {
            type: "string",
            title: "object-src",
            default: "'none'",
        },
        frame_src: {
            type: "string",
            title: "frame-src",
            default: "'none'",
        },
        frame_ancestors: {
            type: "string",
            title: "frame-ancestors",
            default: "'none'",
        },
        form_action: {
            type: "string",
            title: "form-action",
            default: "'self'",
        },
    }
}

const securityHeadersConfigSchema = {
    title: "Security Headers Configuration",
    type: "object",
    properties: {
        hsts_enabled: {
            type: "boolean",
            title: "Enable HSTS",
            default: false,
        },
        hsts_max_age: {
            type: "integer",
            title: "HSTS Max-Age (seconds)",
            default: 31536000,
        },
        hsts_include_subdomains: {
            type: "boolean",
            title: "Include Subdomains in HSTS",
            default: true,
        },
        hsts_preload: {
            type: "boolean",
            title: "Preload HSTS",
            default: false,
        },
        x_xss_protection: {
            type: "boolean",
            title: "Enable X-XSS-Protection",
            default: true,
        },
        x_content_type_options: {
            type: "boolean",
            title: "Enable X-Content-Type-Options",
            default: true,
        },
        x_frame_options: {
            type: "string",
            title: "X-Frame-Options",
            enum: ["DENY", "SAMEORIGIN", "ALLOW-FROM"],
            default: "SAMEORIGIN",
        },
        referrer_policy: {
            type: "string",
            title: "Referrer-Policy",
            default: "no-referrer",
        },
        feature_policy: {
            type: "string",
            title: "Feature-Policy",
            default: "geolocation 'self'; microphone 'none'; camera 'none'",
        },
    }
}


const AppStackDetailsPage = () => {
    const item = useLoaderData();
    console.log("AppStackDetailsPage data:", item);

    const kvValues = item ? Object.entries(item?.properties).map((entry) => {
        let value = entry[1];
        if (typeof value === "boolean") {
            value = value ? "true" : "false";
        } else if (value === null || value === undefined || value === "") {
            value = "-";
        } else if (Array.isArray(value)) {
            value = value.join(", ");
        } else if (typeof value === "object") {
            value = JSON.stringify(value);
        }
        return {key: entry[0], value: value}
    }) : [];

    if (!item) {
        return <p className="text-center">No data available this stack.</p>;
    }

    const itemType = "app-stack";
    return (
        <InventoryProvider itemType={itemType} item={item}>
            <MainContent>
                <Header
                    title={item?.id}
                    subtitle={item?.description || "No description available."}>

                    <div className="flex flex-wrap items-center gap-1">
                        <Data data={item} asButton={true}/>
                        <InventoryItemActionButtons item={item} />
                    </div>
                </Header>

                <div className={"grid grid-cols-1 gap-6"}>
                    <div className={"border rounded-lg"}><KeyValueTable data={kvValues} /></div>
                </div>

                <div className={""}>

                    <h4 className={"h4 font-bold mb-1"}>Stack configuration</h4>
                    <div className={"border p-2 mb-4 rounded-lg"}>
                        <AppStackConfig />
                    </div>

                    <h4 className={"h4 font-bold mb-1"}>Stack file</h4>
                    <div className={"border p-2 mb-4 rounded-lg"}>
                        <AppStackStackfile />
                    </div>


                    {/*<MyForm schema={networkConfigSchema} />*/}
                    {/*<MyForm schema={stackNetworkConfigSchema} />*/}
                    {/*<MyForm schema={cspPolicyConfigSchema} />*/}
                    {/*<MyForm schema={securityHeadersConfigSchema} />*/}
                </div>

            </MainContent>
        </InventoryProvider>
    );
};

export default AppStackDetailsPage;