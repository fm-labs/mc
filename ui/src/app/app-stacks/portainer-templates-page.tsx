import React from 'react'
import Header from "@/components/header.tsx";
import {PORTAINER_TEMPLATE_URLS} from "@/constants.ts";
import PortainerTemplatesView from "@/app/app-stacks/portainer-templates-view.tsx";
import MainContent from "@/components/layout/main-content.tsx";

const PortainerTemplatesPage = () => {
    const templateUrls = PORTAINER_TEMPLATE_URLS
    const [templateUrl, setTemplateUrl] = React.useState(templateUrls[0].url)

    return (
        <MainContent>
            <Header title={"Portainer Templates"}>
                <div>
                    <select onChange={(e) => setTemplateUrl(e.target.value)}>
                        {templateUrls.map((templateUrl) => (
                            <option key={templateUrl.url} value={templateUrl.url}>
                                {templateUrl.label}
                            </option>
                        ))}
                    </select>
                </div>
            </Header>

            <PortainerTemplatesView templateUrl={templateUrl}/>
        </MainContent>
    )
}

export default PortainerTemplatesPage
