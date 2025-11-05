import { useContainerHost } from "@/app/containers/components/container-host-provider.tsx";

export const DockerHostError = () => {
    const { error } = useContainerHost();
    if (!error) {
        return null;
    }

    return (
        <span>
            <span className={`inline-block mr-1 w-3 h-3 rounded-full bg-red-500`} title={error}></span>
            {error}
        </span>
    );
};
