import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";
import AppIcon from "@/components/app-icon.tsx";

export const DockerHostSummary = () => {
    const { summary } = useContainerHost();

    if (!summary) {
        return null;
    }

    return (
        <div
            className="flex items-center gap-4 rounded-lg border bg-card px-4 py-2 text-sm text-muted-foreground shadow-sm">
            <div className="flex items-center gap-2">
                <AppIcon icon="container" size={14} />
                <span className="font-medium text-foreground">{summary?.Containers?.length ?? 0}</span>
                <span>containers</span>
            </div>

            <div className="flex items-center gap-2">
                <AppIcon icon="cube-filled" size={14} />
                <span className="font-medium text-foreground">
                    {summary?.Containers?.filter((c: any) => c.State==="running")?.length ?? 0}
                  </span>
                <span>running</span>
            </div>

            <div className="flex items-center gap-2">
                <AppIcon icon="container-image" size={14} />
                <span className="font-medium text-foreground">{summary?.Images?.length ?? 0}</span>
                <span>images</span>
            </div>

            <div className="flex items-center gap-2">
                <AppIcon icon="container-volume" size={14} />
                <span className="font-medium text-foreground">{summary?.Volumes?.length ?? 0}</span>
                <span>volumes</span>
            </div>
        </div>
    );
};
