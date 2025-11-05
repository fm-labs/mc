import { FindingsProvider } from "@/app/findings/components/findings-provider.tsx";
import FindingsTable from "@/app/findings/components/findings-table.tsx";


export default function FindingsPage() {
    return (
        <FindingsProvider>
            <div className="flex flex-col gap-4 p-4 md:gap-6 md:py-6">
                <div className='mb-2 flex flex-wrap items-center justify-between space-y-2 gap-x-4'>
                    <div>
                        <h2 className='text-2xl font-bold tracking-tight'>Findings</h2>
                        <p className='text-muted-foreground'>
                            Here&apos;s a list of findings that might need your attention!
                        </p>
                    </div>
                </div>

                <FindingsTable />
            </div>

        </FindingsProvider>
    );
}
