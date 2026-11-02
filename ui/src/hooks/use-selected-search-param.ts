import * as React from "react";
import { useSearchParams } from "react-router";

/**
 * Keep a selected id in a URL search param (e.g. ?tool=name),
 * so the selection survives reloads and can be linked to.
 */
export function useSelectedSearchParam(param: string): [string | null, (id: string | null) => void] {
    const [searchParams, setSearchParams] = useSearchParams();
    const selected = searchParams.get(param);

    const setSelected = React.useCallback((id: string | null) => {
        setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            if (id) next.set(param, id);
            else next.delete(param);
            return next;
        }, { replace: true });
    }, [param, setSearchParams]);

    return [selected, setSelected];
}
