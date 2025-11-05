import React from "react";


export const ArrayCell = ({ value }: { value: any[] }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);

    if (isExpanded) {
        return <pre
            onClick={() => setIsExpanded(!isExpanded)} className="whitespace-pre-wrap">{JSON.stringify(value, null, 2)}</pre>;
    }

    return <span onClick={() => setIsExpanded(!isExpanded)}>
        <span>[array] ({value.length})</span>
    </span>
}

export const ObjectCell = ({ value }: { value: object }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);

    if (isExpanded) {
        return <pre
            onClick={() => setIsExpanded(!isExpanded)} className="whitespace-pre-wrap">{JSON.stringify(value, null, 2)}</pre>;
    }

    return <span onClick={() => setIsExpanded(!isExpanded)}>
        <span>[object] ({Object.keys(value).length})</span>
    </span>
}
