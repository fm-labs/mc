import { Navigate } from "react-router";

export default function Page() {

    // return (
    //     <MainContent>
    //         <h1>Dashboard</h1>
    //         {/*<SectionCards />*/}
    //         {/*<div className="px-4 lg:px-6">
    //             <ChartAreaInteractive />
    //         </div>*/}
    //         {/*<DataTableExample data={data} />*/}
    //     </MainContent>
    // )

    return <Navigate to={'/infrastructure'} />
}
