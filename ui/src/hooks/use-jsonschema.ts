
const schemaCache: Record<string, any> = {};

const useJsonschema = (url: string) => {

    const [schemaData, setSchemaData] = React.useState<any>(null);

    const fetcher = async () => {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Error fetching JSON schema: ${response.statusText}`);
        }
        return response.json();
    }

    React.useEffect(() => {
        if (schemaCache[url]) {
            setSchemaData(schemaCache[url]);
            return;
        }
        fetcher().then(data => {
            schemaCache[url] = data;
            setSchemaData(data);
        }).catch(error => {
            console.error("Failed to load JSON schema from", url, error);
        });
    }, [url]);

    const schema = React.useMemo(() => {
        if (!schemaData) return null;
        return schemaData;
    }, [schemaData]);

    return {
        schema
    }
}
