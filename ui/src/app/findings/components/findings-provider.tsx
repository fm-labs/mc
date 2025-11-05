import React, { useState } from "react";
import useDialogState from "@/hooks/use-dialog-state.tsx";
import { Finding } from "@/features/findings/findings.types.ts";
import { useApi } from "@/context/api-context.tsx";

type FindingDialogType = "dismiss"

type FindingContextType = {
    open: FindingDialogType | null
    setOpen: (str: FindingDialogType | null) => void
    currentRow: Finding | null
    setCurrentRow: React.Dispatch<React.SetStateAction<Finding | null>>
    filters: Record<string, any>
    fetchFindings: (filters?: Record<string, any>) => Promise<Finding[]>
    findings: Finding[]
}

const FindingContext = React.createContext<FindingContextType | null>(null);

export function FindingsProvider({ children, initialFilters }: { children: React.ReactNode, initialFilters?: Record<string, any> }) {
    const { api } = useApi();
    const [open, setOpen] = useDialogState<FindingDialogType>(null);
    const [currentRow, setCurrentRow] = useState<Finding | null>(null);
    const [filters, ] = useState<Record<string, any>>(initialFilters || {});
    const [findings, setFindings] = useState<Finding[]>([]);

    const fetchFindings = React.useCallback(async (_filters?: Record<string, any>) => {
        try {
            const _mergedFilters = { ...filters, ..._filters };
            const findings = await api.getFindings(_mergedFilters);
            setFindings(findings);
            return findings;
        } catch (error) {
            console.error("Error fetching data:", error);
            return [];
        }
    }, [api, filters]);

    React.useEffect(() => {
        fetchFindings(filters);

        const timer = setInterval(() => {
            fetchFindings(filters);
        }, 60000);

        return () => clearInterval(timer);
    }, [fetchFindings, filters]);

    return (
        <FindingContext value={{ open, setOpen, currentRow, setCurrentRow, filters, fetchFindings, findings }}>
            {children}
        </FindingContext>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useFindings = () => {
    const findingsContext = React.useContext(FindingContext);

    if (!findingsContext) {
        throw new Error("useFinding has to be used within <FindingContext>");
    }

    return findingsContext;
};
