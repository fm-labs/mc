import { Card } from '@/app/inventory/dns-domain/webcheck/components/Form/Card.tsx';
import Row from '@/app/inventory/dns-domain/webcheck/components/Form/Row.tsx';
import { JSX } from "react";

const cardStyles = `
  small { margin-top: 1rem; opacity: 0.5; }
`;

const OpenPortsCard = (props: { data: any, title: string, actionButtons: any }): JSX.Element => {
  const portData = props.data;
  return (
    <Card heading={props.title} actionButtons={props.actionButtons} styles={cardStyles}>
      {portData.openPorts.map((port: any) => (
          <Row key={port} lbl="" val="">
            <span>{port}</span>
          </Row>
        )
      )}
      <br />
      <small>
        Unable to establish connections to:<br />
        {portData.failedPorts.join(', ')}
      </small>
    </Card>
  );
}

export default OpenPortsCard;
