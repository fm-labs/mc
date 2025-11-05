import { Card } from '@/app/inventory/dns-domain/webcheck/components/Form/Card.tsx';
import Row from '@/app/inventory/dns-domain/webcheck/components/Form/Row.tsx';
import type { ReactNode } from 'react';
import { JSX } from "react";

const HeadersCard = (props: { data: any, title: string, actionButtons: ReactNode }): JSX.Element => {
  const headers = props.data;
  return (
    <Card heading={props.title} styles="grid-row: span 2;" actionButtons={props.actionButtons}>
      {
        Object.keys(headers).map((header: string, index: number) => {
          return (
            <Row key={`header-${index}`} lbl={header} val={headers[header]} />
          )
        })
      }
    </Card>
  );
}

export default HeadersCard;
