import { useFindings } from "@/app/findings/components/findings-provider.tsx";
import { DataTableGeneric } from "@/components/data-table/data-table-generic.tsx";
import { findingsTableColumns } from "@/app/findings/components/findings-table-columns.tsx";

const FindingsTable = () => {
    const { findings } = useFindings()

    return (
        <div>
            {findings ? <DataTableGeneric columns={findingsTableColumns} data={findings} />
                :<p className="text-center">No findings.</p>}
        </div>
    );
};

export default FindingsTable;
