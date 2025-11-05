import { useState, useEffect, JSX } from "react";
import { useParams, Cookie } from "react-router";
import styled from "@emotion/styled";
import { ToastContainer } from "react-toastify";
import Masonry from "react-masonry-css";

//import colors from './webcheck/styles/colors';
// import Heading from './webcheck/components/Form/Heading';
// import Modal from './webcheck/components/Form/Modal';
// import Footer from './webcheck/components/misc/Footer';
// import Nav from './webcheck/components/Form/Nav';
// import type { RowProps }  from './webcheck/components/Form/Row';
//
// import Loader from './webcheck/components/misc/Loader';
// import ErrorBoundary from './webcheck/components/misc/ErrorBoundary';
// import SelfScanMsg from './webcheck/components/misc/SelfScanMsg';
// import DocContent from './webcheck/components/misc/DocContent';
// import ProgressBar, { type LoadingJob, type LoadingState, initialJobs } from './webcheck/components/misc/ProgressBar';
// import ActionButtons from './webcheck/components/misc/ActionButtons';
// import AdditionalResources from './webcheck/components/misc/AdditionalResources';
// import ViewRaw from './webcheck/components/misc/ViewRaw';

import ServerLocationCard from "./webcheck/components/Results/ServerLocation.tsx";
import ServerInfoCard from "./webcheck/components/Results/ServerInfo.tsx";
import HostNamesCard from "./webcheck/components/Results/HostNames.tsx";
import WhoIsCard from "./webcheck/components/Results/WhoIs.tsx";
import LighthouseCard from "./webcheck/components/Results/Lighthouse.tsx";
import ScreenshotCard from "./webcheck/components/Results/Screenshot.tsx";
import SslCertCard from "./webcheck/components/Results/SslCert.tsx";
import HeadersCard from "./webcheck/components/Results/Headers.tsx";
import CookiesCard from "./webcheck/components/Results/Cookies.tsx";
import RobotsTxtCard from "./webcheck/components/Results/RobotsTxt.tsx";
import DnsRecordsCard from "./webcheck/components/Results/DnsRecords.tsx";
import RedirectsCard from "./webcheck/components/Results/Redirects.tsx";
import TxtRecordCard from "./webcheck/components/Results/TxtRecords.tsx";
import ServerStatusCard from "./webcheck/components/Results/ServerStatus.tsx";
import OpenPortsCard from "./webcheck/components/Results/OpenPorts.tsx";
import TraceRouteCard from "./webcheck/components/Results/TraceRoute.tsx";
import CarbonFootprintCard from "./webcheck/components/Results/CarbonFootprint.tsx";
import SiteFeaturesCard from "./webcheck/components/Results/SiteFeatures.tsx";
import DnsSecCard from "./webcheck/components/Results/DnsSec.tsx";
import HstsCard from "./webcheck/components/Results/Hsts.tsx";
import SitemapCard from "./webcheck/components/Results/Sitemap.tsx";
import DomainLookup from "./webcheck/components/Results/DomainLookup.tsx";
import DnsServerCard from "./webcheck/components/Results/DnsServer.tsx";
import TechStackCard from "./webcheck/components/Results/TechStack.tsx";
import SecurityTxtCard from "./webcheck/components/Results/SecurityTxt.tsx";
import ContentLinksCard from "./webcheck/components/Results/ContentLinks.tsx";
import SocialTagsCard from "./webcheck/components/Results/SocialTags.tsx";
import MailConfigCard from "./webcheck/components/Results/MailConfig.tsx";
import HttpSecurityCard from "./webcheck/components/Results/HttpSecurity.tsx";
import FirewallCard from "./webcheck/components/Results/Firewall.tsx";
import ArchivesCard from "./webcheck/components/Results/Archives.tsx";
import RankCard from "./webcheck/components/Results/Rank.tsx";
import BlockListsCard from "./webcheck/components/Results/BlockLists.tsx";
import ThreatsCard from "./webcheck/components/Results/Threats.tsx";
import TlsCipherSuitesCard from "./webcheck/components/Results/TlsCipherSuites.tsx";
import TlsIssueAnalysisCard from "./webcheck/components/Results/TlsIssueAnalysis.tsx";
import TlsClientSupportCard from "./webcheck/components/Results/TlsClientSupport.tsx";

// import keys from './webcheck/utils/get-keys';
// import { determineAddressType, type AddressType } from './webcheck/utils/address-type-checker';
import useMotherHook from "./webcheck/hooks/motherOfAllHooks.ts";
import { AddressType, determineAddressType } from "@/app/inventory/dns-domain/webcheck/utils/address-type-checker.ts";
import {
    applyWhoIsResults, getLocation,
    parseShodanResults, ServerLocation,
    ShodanResults,
    Whois,
} from "@/app/inventory/dns-domain/webcheck/utils/result-processor.ts";
import keys from "@/app/inventory/dns-domain/webcheck/utils/get-keys.ts";
import { WEBCHECK_API_BASE_URL } from "@/constants.ts";
import ErrorBoundary from "@/components/error-boundary.tsx";

const ResultsOuter = styled.div`
    display: flex;
    flex-direction: column;

    .masonry-grid {
        display: flex;
        width: auto;
    }

    .masonry-grid-col section {
        margin: 0 0.5rem 1rem 0.5rem;
    }
`;

const ResultsContent = styled.section`
    display: grid;
    //grid-auto-flow: dense;
    //grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    //gap: 1rem;
    margin: auto;
    //width: 95vw;
    //width: calc(100% - 2rem);
    //padding-bottom: 1rem;
`;

const Results = (props: { address?: string }): JSX.Element => {

    const address = props.address || useParams().urlToScan || "";
    const [addressType, setAddressType] = useState<AddressType>("empt");

    const parseJson = (response: Response): Promise<any> => {
        return new Promise((resolve) => {
            response.json()
                .then(data => resolve(data))
                .catch(error => resolve(
                    {
                        error: `Failed to get a valid response 😢\n`
                            + "This is likely due the target not exposing the required data, "
                            + "or limitations in imposed by the infrastructure this instance "
                            + "of Web Check is running on.\n\n"
                            + `Error info:\n${error}`,
                    },
                ));
        });
    };

    const urlTypeOnly = ["url"] as AddressType[]; // Many jobs only run with these address types

    const api = WEBCHECK_API_BASE_URL; // Where is the API hosted?

    // Fetch and parse IP address for given URL
    const [ipAddress, setIpAddress] = useMotherHook({
        jobId: "get-ip",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/get-ip?url=${address}`)
            .then(res => parseJson(res))
            .then(res => res.ip),
    });

    useEffect(() => {
        if (!addressType || addressType==="empt") {
            setAddressType(determineAddressType(address || ""));
        }
        if (addressType==="ipV4" && address) {
            setIpAddress(address);
        }
    }, [address, addressType, setIpAddress]);

    // Get IP address location info
    const [locationResults, updateLocationResults] = useMotherHook<ServerLocation>({
        jobId: "location",

        addressInfo: { address: ipAddress, addressType: "ipV4", expectedAddressTypes: ["ipV4", "ipV6"] },
        fetchRequest: () => fetch(`https://ipapi.co/${ipAddress}/json/`)
            .then(res => parseJson(res))
            .then(res => getLocation(res)),
    });

    // Fetch and parse SSL certificate info
    const [sslResults, updateSslResults] = useMotherHook({
        jobId: "ssl",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/ssl?url=${address}`).then((res) => parseJson(res)),
    });

    // Run a manual whois lookup on the domain
    const [domainLookupResults, updateDomainLookupResults] = useMotherHook({
        jobId: "domain",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/whois?url=${address}`).then(res => parseJson(res)),
    });

    // Fetch and parse Lighthouse performance data
    const [lighthouseResults, updateLighthouseResults] = useMotherHook({
        jobId: "quality",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/quality?url=${address}`)
            .then(res => parseJson(res))
            .then(res => res?.lighthouseResult || { error: res.error || "No Data" }),
    });

    // Get the technologies used to build site, using Wappalyzer
    const [techStackResults, updateTechStackResults] = useMotherHook({
        jobId: "tech-stack",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/tech-stack?url=${address}`).then(res => parseJson(res)),
    });

    // Get hostnames and associated domains from Shodan
    const [shoadnResults, updateShodanResults] = useMotherHook<ShodanResults>({
        jobId: ["hosts", "server-info"],

        addressInfo: { address: ipAddress, addressType: "ipV4", expectedAddressTypes: ["ipV4", "ipV6"] },
        fetchRequest: () => fetch(`https://api.shodan.io/shodan/host/${ipAddress}?key=${keys.shodan}`)
            .then(res => parseJson(res))
            .then(res => parseShodanResults(res)),
    });

    // Fetch and parse cookies info
    const [cookieResults, updateCookieResults] = useMotherHook<{ cookies: Cookie[] }>({
        jobId: "cookies",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/cookies?url=${address}`)
            .then(res => parseJson(res)),
    });

    // Fetch and parse headers
    const [headersResults, updateHeadersResults] = useMotherHook({
        jobId: "headers",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/headers?url=${address}`).then(res => parseJson(res)),
    });

    // Fetch and parse DNS records
    const [dnsResults, updateDnsResults] = useMotherHook({
        jobId: "dns",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/dns?url=${address}`).then(res => parseJson(res)),
    });

    // Get HTTP security
    const [httpSecurityResults, updateHttpSecurityResults] = useMotherHook({
        jobId: "http-security",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/http-security?url=${address}`).then(res => parseJson(res)),
    });

    // Get social media previews, from a sites social meta tags
    const [socialTagResults, updateSocialTagResults] = useMotherHook({
        jobId: "social-tags",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/social-tags?url=${address}`).then(res => parseJson(res)),
    });

    // Get trace route for a given hostname
    const [traceRouteResults, updateTraceRouteResults] = useMotherHook({
        jobId: "trace-route",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/trace-route?url=${address}`).then(res => parseJson(res)),
    });

    // Get a websites listed pages, from sitemap
    const [securityTxtResults, updateSecurityTxtResults] = useMotherHook({
        jobId: "security-txt",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/security-txt?url=${address}`).then(res => parseJson(res)),
    });

    // Get the DNS server(s) for a domain, and test DoH/DoT support
    const [dnsServerResults, updateDnsServerResults] = useMotherHook({
        jobId: "dns-server",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/dns-server?url=${address}`).then(res => parseJson(res)),
    });

    // Get the WAF and Firewall info for a site
    const [firewallResults, updateFirewallResults] = useMotherHook({
        jobId: "firewall",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/firewall?url=${address}`).then(res => parseJson(res)),
    });

    // Get DNSSEC info
    const [dnsSecResults, updateDnsSecResults] = useMotherHook({
        jobId: "dnssec",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/dnssec?url=${address}`).then(res => parseJson(res)),
    });

    // Check if a site is on the HSTS preload list
    const [hstsResults, updateHstsResults] = useMotherHook({
        jobId: "hsts",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/hsts?url=${address}`).then(res => parseJson(res)),
    });

    // Check if a host is present on the URLHaus malware list
    const [threatResults, updateThreatResults] = useMotherHook({
        jobId: "threats",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/threats?url=${address}`).then(res => parseJson(res)),
    });

    // Get mail config for server, based on DNS records
    const [mailConfigResults, updateMailConfigResults] = useMotherHook({
        jobId: "mail-config",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/mail-config?url=${address}`).then(res => parseJson(res)),
    });

    // Get list of archives from the Wayback Machine
    const [archivesResults, updateArchivesResults] = useMotherHook({
        jobId: "archives",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/archives?url=${address}`).then(res => parseJson(res)),
    });

    // Get website's global ranking, from Tranco
    const [rankResults, updateRankResults] = useMotherHook({
        jobId: "rank",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/rank?url=${address}`).then(res => parseJson(res)),
    });

    // Take a screenshot of the website
    const [screenshotResult, updateScreenshotResult] = useMotherHook({
        jobId: "screenshot",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/screenshot?url=${address}`).then(res => parseJson(res)),
    });

    // Get TLS security info, from Mozilla Observatory
    const [tlsResults, updateTlsResults] = useMotherHook({
        jobId: ["tls-cipher-suites", "tls-security-config", "tls-client-support"],

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/tls?url=${address}`).then(res => parseJson(res)),
    });

    // Fetches URL redirects
    const [redirectResults, updateRedirectResults] = useMotherHook({
        jobId: "redirects",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/redirects?url=${address}`).then(res => parseJson(res)),
    });

    // Get list of links included in the page content
    const [linkedPagesResults, updateLinkedPagesResults] = useMotherHook({
        jobId: "linked-pages",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/linked-pages?url=${address}`).then(res => parseJson(res)),
    });

    // Fetch and parse crawl rules from robots.txt
    const [robotsTxtResults, updateRobotsTxtResults] = useMotherHook<{ robots: any[] }>({
        jobId: "robots-txt",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/robots-txt?url=${address}`)
            .then(res => parseJson(res)),
    });

    // Get current status and response time of server
    const [serverStatusResults, updateServerStatusResults] = useMotherHook({
        jobId: "status",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/status?url=${address}`).then(res => parseJson(res)),
    });

    // Check for open ports
    const [portsResults, updatePortsResults] = useMotherHook({
        jobId: "ports",

        addressInfo: { address: ipAddress, addressType: "ipV4", expectedAddressTypes: ["ipV4", "ipV6"] },
        fetchRequest: () => fetch(`${api}/ports?url=${ipAddress}`)
            .then(res => parseJson(res)),
    });

    // Fetch and parse domain whois results
    const [whoIsResults, updateWhoIsResults] = useMotherHook<Whois | { error: string }>({
        jobId: "whois",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`https://api.whoapi.com/?domain=${address}&r=whois&apikey=${keys.whoApi}`)
            .then(res => parseJson(res))
            .then(res => applyWhoIsResults(res)),
    });

    // Fetches DNS TXT records
    const [txtRecordResults, updateTxtRecordResults] = useMotherHook({
        jobId: "txt-records",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/txt-records?url=${address}`).then(res => parseJson(res)),
    });

    // Check site against DNS blocklists
    const [blockListsResults, updateBlockListsResults] = useMotherHook({
        jobId: "block-lists",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/block-lists?url=${address}`).then(res => parseJson(res)),
    });

    // Get a websites listed pages, from sitemap
    const [sitemapResults, updateSitemapResults] = useMotherHook({
        jobId: "sitemap",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/sitemap?url=${address}`).then(res => parseJson(res)),
    });

    // Fetch carbon footprint data for a given site
    const [carbonResults, updateCarbonResults] = useMotherHook({
        jobId: "carbon",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/carbon?url=${address}`).then(res => parseJson(res)),
    });

    // Get site features from BuiltWith
    const [siteFeaturesResults, updateSiteFeaturesResults] = useMotherHook({
        jobId: "features",

        addressInfo: { address, addressType, expectedAddressTypes: urlTypeOnly },
        fetchRequest: () => fetch(`${api}/features?url=${address}`)
            .then(res => parseJson(res))
            .then(res => {
                if (res.Errors && res.Errors.length > 0) {
                    return { error: `No data returned, because ${res.Errors[0].Message || "API lookup failed"}` };
                }
                return res;
            }),
    });


    // A list of state sata, corresponding component and title for each card
    const resultCardData = [
        {
            id: "location",
            title: "Server Location",
            result: locationResults,
            Component: ServerLocationCard,
            refresh: updateLocationResults,
            tags: ["server"],
            enabled: true
        },
        {
            id: "ssl",
            title: "SSL Certificate",
            result: sslResults,
            Component: SslCertCard,
            refresh: updateSslResults,
            tags: ["server", "security"],
            enabled: true
        }, {
            id: "domain",
            title: "Domain Whois",
            result: domainLookupResults,
            Component: DomainLookup,
            refresh: updateDomainLookupResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "quality",
            title: "Quality Summary",
            result: lighthouseResults,
            Component: LighthouseCard,
            refresh: updateLighthouseResults,
            tags: ["client"],
            enabled: false
        }, {
            id: "tech-stack",
            title: "Tech Stack",
            result: techStackResults,
            Component: TechStackCard,
            refresh: updateTechStackResults,
            tags: ["client", "meta"],
            enabled: false
        }, {
            id: "server-info",
            title: "Server Info",
            result: shoadnResults?.serverInfo,
            Component: ServerInfoCard,
            refresh: updateShodanResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "cookies",
            title: "Cookies",
            result: cookieResults,
            Component: CookiesCard,
            refresh: updateCookieResults,
            tags: ["client", "security"],
            enabled: true
        }, {
            id: "headers",
            title: "Headers",
            result: headersResults,
            Component: HeadersCard,
            refresh: updateHeadersResults,
            tags: ["client", "security"],
            enabled: true
        }, {
            id: "dns",
            title: "DNS Records",
            result: dnsResults,
            Component: DnsRecordsCard,
            refresh: updateDnsResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "hosts",
            title: "Host Names",
            result: shoadnResults?.hostnames,
            Component: HostNamesCard,
            refresh: updateShodanResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "http-security",
            title: "HTTP Security",
            result: httpSecurityResults,
            Component: HttpSecurityCard,
            refresh: updateHttpSecurityResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "social-tags",
            title: "Social Tags",
            result: socialTagResults,
            Component: SocialTagsCard,
            refresh: updateSocialTagResults,
            tags: ["client", "meta"],
            enabled: true
        }, {
            id: "trace-route",
            title: "Trace Route",
            result: traceRouteResults,
            Component: TraceRouteCard,
            refresh: updateTraceRouteResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "security-txt",
            title: "Security.Txt",
            result: securityTxtResults,
            Component: SecurityTxtCard,
            refresh: updateSecurityTxtResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "dns-server",
            title: "DNS Server",
            result: dnsServerResults,
            Component: DnsServerCard,
            refresh: updateDnsServerResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "firewall",
            title: "Firewall",
            result: firewallResults,
            Component: FirewallCard,
            refresh: updateFirewallResults,
            tags: ["server", "security"],
            enabled: true
        }, {
            id: "dnssec",
            title: "DNSSEC",
            result: dnsSecResults,
            Component: DnsSecCard,
            refresh: updateDnsSecResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "hsts",
            title: "HSTS Check",
            result: hstsResults,
            Component: HstsCard,
            refresh: updateHstsResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "threats",
            title: "Threats",
            result: threatResults,
            Component: ThreatsCard,
            refresh: updateThreatResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "mail-config",
            title: "Email Configuration",
            result: mailConfigResults,
            Component: MailConfigCard,
            refresh: updateMailConfigResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "archives",
            title: "Archive History",
            result: archivesResults,
            Component: ArchivesCard,
            refresh: updateArchivesResults,
            tags: ["meta"],
            enabled: true
        }, {
            id: "rank",
            title: "Global Ranking",
            result: rankResults,
            Component: RankCard,
            refresh: updateRankResults,
            tags: ["meta"],
            enabled: false
        }, {
            id: "screenshot",
            title: "Screenshot",
            result: screenshotResult || lighthouseResults?.fullPageScreenshot?.screenshot,
            Component: ScreenshotCard,
            refresh: updateScreenshotResult,
            tags: ["client", "meta"],
            enabled: false
        }, {
            id: "tls-cipher-suites",
            title: "TLS Cipher Suites",
            result: tlsResults,
            Component: TlsCipherSuitesCard,
            refresh: updateTlsResults,
            tags: ["server", "security"],
            enabled: true
        }, {
            id: "tls-security-config",
            title: "TLS Security Issues",
            result: tlsResults,
            Component: TlsIssueAnalysisCard,
            refresh: updateTlsResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "tls-client-support",
            title: "TLS Handshake Simulation",
            result: tlsResults,
            Component: TlsClientSupportCard,
            refresh: updateTlsResults,
            tags: ["security"],
            enabled: true
        }, {
            id: "redirects",
            title: "Redirects",
            result: redirectResults,
            Component: RedirectsCard,
            refresh: updateRedirectResults,
            tags: ["meta"],
            enabled: true
        }, {
            id: "linked-pages",
            title: "Linked Pages",
            result: linkedPagesResults,
            Component: ContentLinksCard,
            refresh: updateLinkedPagesResults,
            tags: ["client", "meta"],
            enabled: true
        }, {
            id: "robots-txt",
            title: "Crawl Rules",
            result: robotsTxtResults,
            Component: RobotsTxtCard,
            refresh: updateRobotsTxtResults,
            tags: ["meta"],
            enabled: true
        }, {
            id: "status",
            title: "Server Status",
            result: serverStatusResults,
            Component: ServerStatusCard,
            refresh: updateServerStatusResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "ports",
            title: "Open Ports",
            result: portsResults,
            Component: OpenPortsCard,
            refresh: updatePortsResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "whois",
            title: "Domain Info",
            result: whoIsResults,
            Component: WhoIsCard,
            refresh: updateWhoIsResults,
            tags: ["server"],
            enabled: false
        }, {
            id: "txt-records",
            title: "TXT Records",
            result: txtRecordResults,
            Component: TxtRecordCard,
            refresh: updateTxtRecordResults,
            tags: ["server"],
            enabled: true
        }, {
            id: "block-lists",
            title: "Block Lists",
            result: blockListsResults,
            Component: BlockListsCard,
            refresh: updateBlockListsResults,
            tags: ["security", "meta"],
            enabled: true
        }, {
            id: "features",
            title: "Site Features",
            result: siteFeaturesResults,
            Component: SiteFeaturesCard,
            refresh: updateSiteFeaturesResults,
            tags: ["meta"],
            enabled: false
        }, {
            id: "sitemap",
            title: "Pages",
            result: sitemapResults,
            Component: SitemapCard,
            refresh: updateSitemapResults,
            tags: ["meta"],
            enabled: true
        }, {
            id: "carbon",
            title: "Carbon Footprint",
            result: carbonResults,
            Component: CarbonFootprintCard,
            refresh: updateCarbonResults,
            tags: ["meta"],
            enabled: false
        },
    ];

    return (
        <ResultsOuter>
            <ResultsContent>
                <Masonry
                    breakpointCols={{
                        10000: 12,
                        4000: 9,
                        3600: 8,
                        3200: 7,
                        2800: 6,
                        2400: 5,
                        2000: 4,
                        1600: 3,
                        1200: 2,
                        800: 1,
                    }}
                    className="masonry-grid"
                    columnClassName="masonry-grid-col">
                    {
                        resultCardData
                            .filter(({ enabled }) => enabled)
                            .map(({ title, result, Component }, index: number) => {
                                const show = true;
                                //const show = (tags.length === 0 || tags.some(tag => tags.includes(tag)))
                                //&& title.toLowerCase().includes(searchTerm.toLowerCase())
                                //&& (result && !result.error);
                                if (!result) {
                                  return <div>Loading {title}...</div>
                                } else if (result.error) {
                                    return (
                                        <div className='rounded-md border text-sm border-red-600 bg-red-50 p-2 mx-2 mb-2' key={`error-${index}`}>
                                            <h4 className='font-bold text-red-600'>Error: {title}</h4>
                                            <p className='text-red-600'>{result ? (result?.error) : 'Unknown error'}</p>
                                        </div>
                                    )
                                }

                                // if (result && result.error) {
                                //     return <div className="rounded-md border text-sm border-red-600 bg-red-50 p-2 mb-2"
                                //                 key={`error-${index}`}>
                                //         <h4 className="font-bold text-red-600">Error loading {title}</h4>
                                //         <p className="text-red-600">{result.error}</p>
                                //     </div>;
                                // }

                                return show ? (
                                    <ErrorBoundary title={title} key={`eb-${index}`}>
                                        <Component
                                            key={`${title}-${index}`}
                                            data={{ ...result }}
                                            title={title}
                                            actionButtons={undefined}
                                        />
                                    </ErrorBoundary>
                                ):null;
                            })
                    }
                </Masonry>
            </ResultsContent>
            {/*<ViewRaw everything={resultCardData} />*/}
            <ToastContainer limit={3} draggablePercent={60} autoClose={2500} theme="dark" position="bottom-right" />
        </ResultsOuter>
    );
};

export default Results;
