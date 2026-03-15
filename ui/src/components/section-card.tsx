import React, {PropsWithChildren} from 'react';

const SectionCard = (props: PropsWithChildren<{title?: string, headerEl?: React.ReactNode}>) => {

    const headerEl = props.headerEl ? props.headerEl : (props.title ? <h2 className={"text-lg font-semibold mb-2"}>{props.title}</h2> : null);

    return (
        <div className={"border-3 rounded-lg p-4"}>
            {headerEl && <div className={"mb-4"}>{headerEl}</div>}
            {props.children}
        </div>
    );
};

export default SectionCard;