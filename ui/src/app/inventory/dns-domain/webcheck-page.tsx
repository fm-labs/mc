import Results from "@/app/inventory/dns-domain/webcheck.tsx";
import Header from "@/components/header.tsx";
import { useParams } from "react-router";
import MainContent from "@/components/layout/main-content.tsx";

const WebcheckPage = () => {
    const { domain } = useParams<{domain: string}>()

    if (!domain) {
        return <div>No domain</div>;
    }

    return (
        <MainContent>
            <Header title="Webcheck" subtitle={domain}>
                <input type="text" defaultValue={domain} className="input-bordered input w-full max-w-xs" />
            </Header>

            <Results address={'https://' + domain} />
        </MainContent>
    );
};

export default WebcheckPage;
