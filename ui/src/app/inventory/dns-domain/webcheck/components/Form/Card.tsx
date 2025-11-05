import styled from '@emotion/styled';

import { JSX, type ReactNode } from "react";
import colors from "@/app/inventory/dns-domain/webcheck/styles/colors.ts";

export const StyledCard = styled.section<{ styles?: string}>`
  background: ${colors.backgroundLighter};
  color: ${colors.textColor};
  box-shadow: 4px 4px 0px ${colors.bgShadowColor};
  border-radius: 8px;
  padding: 1rem;
  position: relative;
  margin: 0.5rem;
  max-height: 64rem;
  overflow: auto;
  ${props => props.styles}
`;

interface CardProps {
  children: ReactNode;
  heading?: string,
  styles?: string;
  actionButtons?: ReactNode | undefined;
};

export const Card = (props: CardProps): JSX.Element => {
  const { children, heading, styles, actionButtons } = props;
  return (
      <StyledCard styles={styles}>
        { actionButtons && actionButtons }
        { heading && <div className="inner-heading">{heading}</div> }
        {children}
      </StyledCard>
  );
}

export default StyledCard;
