
import { Card } from '@/app/inventory/dns-domain/webcheck/components/Form/Card.tsx';
import Row from '@/app/inventory/dns-domain/webcheck/components/Form/Row.tsx';
import { JSX } from "react";

const BlockListsCard = (props: {data: any, title: string, actionButtons: any }): JSX.Element => {
  const blockLists = props.data.blocklists;
  return (
    <Card heading={props.title} actionButtons={props.actionButtons}>
      { blockLists.map((blocklist: any, blockIndex: number) => (
        <Row
          title={blocklist.serverIp}
          lbl={blocklist.server}
          val={blocklist.isBlocked ? '❌ Blocked' : '✅ Not Blocked'}
          key={`blocklist-${blockIndex}-${blocklist.serverIp}`}
        />
      ))}
    </Card>
  );
}

export default BlockListsCard;
