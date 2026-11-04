import React from "react";
import { IconUpload } from "@tabler/icons-react";
import { toast } from "sonner";
import { useApi } from "@/context/api-context.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Input } from "@/components/ui/input.tsx";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog.tsx";
import { AppSpecDetails } from "@/features/apps/apps.types.ts";
import { apiErrorMessage } from "@/features/apps/apps-errors.ts";

export const BUNDLE_ACCEPT = ".tar.gz,.tgz,.tar,application/gzip,application/x-gzip,application/x-tar";

type Props = {
    appId: string;
    // set while the editor has unsaved changes
    disabledReason?: string | null;
    onUploaded: (details: AppSpecDetails) => void;
};

/**
 * Button + dialog to extract a bundle (tar.gz) over an existing app's folder.
 */
const AppBundleUploadDialog = ({ appId, disabledReason, onUploaded }: Props) => {
    const { api } = useApi();
    const [open, setOpen] = React.useState(false);
    const [file, setFile] = React.useState<File | null>(null);
    const [uploading, setUploading] = React.useState(false);

    const handleOpenChange = (next: boolean) => {
        if (uploading) return;
        setOpen(next);
        if (!next) setFile(null);
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        try {
            const details = await api.updateAppFromBundle(appId, file);
            toast.success(`Updated ${appId} from ${file.name}`);
            onUploaded(details);
            setOpen(false);
            setFile(null);
        } catch (error) {
            toast.error(`Upload failed: ${apiErrorMessage(error)}`);
        } finally {
            setUploading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" disabled={!!disabledReason} title={disabledReason ?? undefined}>
                    <IconUpload size={16} /> Upload bundle
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Update from bundle</DialogTitle>
                    <DialogDescription>
                        A tar.gz with a compose file at its root and optional extra files.
                    </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-3 text-sm">
                    <Input
                        type="file"
                        accept={BUNDLE_ACCEPT}
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        disabled={uploading}
                    />
                    <ul className="list-disc pl-5 text-muted-foreground">
                        <li>Files in the bundle replace the same files in the app folder.</li>
                        <li>Other files in the app folder are kept, e.g. bind mount data.</li>
                        <li>Volumes, networks, routing and environment are kept.</li>
                        <li>Run <strong>Up</strong> afterwards to apply the change.</li>
                    </ul>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={uploading}>Cancel</Button>
                    <Button onClick={handleUpload} disabled={!file || uploading}>
                        {uploading ? "Uploading..." : "Upload"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default AppBundleUploadDialog;
