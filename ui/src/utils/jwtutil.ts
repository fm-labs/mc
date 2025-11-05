
export const isJwtExpired = (token: string): boolean => {
    if (!token) return true;

    const parts = token.split('.');
    if (parts.length !== 3) {
        console.error("Invalid JWT token format");
        return true;
    }

    try {
        const payload = JSON.parse(atob(parts[1]));
        if (!payload.exp) {
            console.error("JWT token has no exp claim");
            return true;
        }

        const now = Math.floor(Date.now() / 1000);
        const expired = now >= payload.exp;
        if (expired) {
            console.warn("JWT token is expired", "expired at", new Date(payload.exp * 1000).toISOString());
        } else {
            console.log("JWT token is valid", "expires at", new Date(payload.exp * 1000).toISOString());
        }
        return expired;
    } catch (e) {
        console.error("Error parsing JWT token:", e);
        return true;
    }
}

export const decodeJwt = (token: string): any | null => {
    if (!token) return null;

    const parts = token.split('.');
    if (parts.length !== 3) {
        console.error("Invalid JWT token format");
        return null;
    }

    try {
        return JSON.parse(atob(parts[1]));
    } catch (e) {
        console.error("Error parsing JWT token:", e);
        return null;
    }
}
