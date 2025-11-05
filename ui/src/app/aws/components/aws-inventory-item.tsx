import { AwsInventoryItemFull } from "@/app/aws/types.ts";
import ReactJson from "@microlink/react-json-view";

const AwsInventoryItem = ({item}: {item: AwsInventoryItemFull}) => {
    if (!item) {
        return <div>No item provided</div>;
    }

    const renderProperties = (obj: any, indent: number = 0): React.ReactNode => {
        if (obj === null || obj === undefined) {
            return <span className="text-gray-500">null</span>;
        }
        // if (typeof obj !== 'object') {
        //     return <span>{String(obj)}</span>;
        // }
        const entries = Object.entries(obj);
        return (
            <div style={{ paddingLeft: indent * 4 }}>
                {entries.map(([key, value]) => {
                    if (typeof value === "object" && Array.isArray(value)) {
                        //return '[array]'
                    }
                    else if (typeof value === "object") {
                        //return <div>{key}: (object)</div>
                        return 'x'
                    }
                    else {
                        //return <div>{key}: <span className={"text-muted-foreground"}>{value as string}</span> (string)</div>
                        return '.'
                    }

                    return (
                        <div key={key} className="mb-1 border border-red-400">
                            <strong>{key}:</strong> {renderProperties(value, indent + 1)}
                        </div>
                    );
                })}
            </div>
        );
    }

    return (
        <div>
            {renderProperties(item?.properties)}

            <ReactJson src={item} collapsed={false} enableClipboard={false} displayDataTypes={false} />
        </div>
    );
};

export default AwsInventoryItem;
