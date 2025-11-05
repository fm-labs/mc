import { Card } from '@/app/inventory/dns-domain/webcheck/components/Form/Card.tsx';
import Row from '@/app/inventory/dns-domain/webcheck/components/Form/Row.tsx';
import Heading from '@/app/inventory/dns-domain/webcheck/components/Form/Heading.tsx';
import colors from '@/app/inventory/dns-domain/webcheck/styles/colors.ts';
import { JSX } from "react";

const cardStyles = `
  small { margin-top: 1rem; opacity: 0.5; }
  a {
    color: ${colors.textColor};
  }
  details {
    // display: inline;
    display: flex;
    transition: all 0.2s ease-in-out;
    h3 {
      display: inline;
    }
    summary {
      padding: 0;
      margin: 1rem 0 0 0;
      cursor: pointer;
    }
    summary:before {
      content: "►";
      position: absolute;
      margin-left: -1rem;
      color: ${colors.primary};
      cursor: pointer;
    }
    &[open] summary:before {
      content: "▼";
    }
  }
`;

const getPathName = (link: string) => {
  try {
    const url = new URL(link);
    return url.pathname;
  } catch(e) {
    return link;
  }
};

const ContentLinksCard = (props: { data: any, title: string, actionButtons: any }): JSX.Element => {
  const internal = props.data.internal || [];
  const external = props.data.external || [];
  return (
    <Card heading={props.title} actionButtons={props.actionButtons} styles={cardStyles}>
      <Heading as="h3" size="small" color={colors.primary}>Summary</Heading>
      <Row lbl="Internal Link Count" val={internal.length} />
      <Row lbl="External Link Count" val={external.length} />
      { internal && internal.length > 0 && (
        <details>
          <summary><Heading as="h3" size="small" color={colors.primary}>Internal Links</Heading></summary>
          {internal.map((link: string) => (
          <Row key={link} lbl="" val="">
            <a href={link} target="_blank" rel="noreferrer">{getPathName(link)}</a>
          </Row>
        ))}
        </details>
      )}
      { external && external.length > 0 && (
        <details>
          <summary><Heading as="h3" size="small" color={colors.primary}>External Links</Heading></summary>
          {external.map((link: string) => (
            <Row key={link} lbl="" val="">
              <a href={link} target="_blank" rel="noreferrer">{link}</a>
            </Row>
          ))}
        </details>
      )}
    </Card>
  );
}

export default ContentLinksCard;
