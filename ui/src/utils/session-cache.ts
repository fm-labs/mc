const storeDataInLocalSessionStorage = (key: string, data: any) => {
    if (typeof window!=="undefined" && window.sessionStorage) {
        try {
            window.sessionStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.warn("Could not store data in sessionStorage:", e);
        }
    }
};

const readDataFromLocalSessionStorage = (key: string): any | null => {
    if (typeof window!=="undefined" && window.sessionStorage) {
        try {
            const item = window.sessionStorage.getItem(key);
            if (item) {
                return JSON.parse(item);
            }
        } catch (e) {
            console.warn("Could not read data from sessionStorage:", e);
        }
    }
    return null;
};

export const cached = (key: string, fetchFunction: () => Promise<any>, ttl: number = 0, forceFetch?: boolean): Promise<any> => {
    if (typeof window!=="undefined" && window.sessionStorage && !forceFetch) {
        //console.log("Checking cache for key:", key);
        try {
            const item = readDataFromLocalSessionStorage(key);
            if (item) {
                const { timestamp, data } = item;
                if (data && (!ttl || (Date.now() - timestamp) < ttl)) {
                    return Promise.resolve(data);
                } else {
                    //console.log("Cache expired for key:", key);
                }
            } else {
                //console.log("No cache item found for key:", key);
            }
        } catch (e) {
            //console.warn("Could not get data from sessionStorage:", e);
        }
    }
    return fetchFunction().then(data => {
        const cacheItem = {
            timestamp: Date.now(),
            data: data,
        };
        //console.log("New Cache item: ", key, cacheItem);
        storeDataInLocalSessionStorage(key, cacheItem);
        return data;
    });
};
