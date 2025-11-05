import AwsInventory from "@/app/aws/components/aws-inventory.tsx";
import { AwsInventoryProvider } from "@/app/aws/aws-inventory-provider.tsx";
import MainContent from "@/components/layout/main-content.tsx";
import AwsInventoryFilterbar from "@/app/aws/components/aws-inventory-filterbar.tsx";

const AwsInventoryPage = () => {

    return <MainContent>
        <AwsInventoryProvider>
            <AwsInventoryFilterbar />
            <AwsInventory />
        </AwsInventoryProvider>
    </MainContent>
};

export default AwsInventoryPage;
