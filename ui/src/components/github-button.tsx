import React from "react";
import { Button } from "@/components/ui/button.tsx";

const GithubButton = () => {
    return (
        <Button variant="outline" asChild size="sm" className="hidden sm:flex">
            <a
                href="https://github.com/fm-labs/mc"
                rel="noopener noreferrer"
                target="_blank"
                className="dark:text-foreground"
            >
                GitHub
            </a>
        </Button>
    );
};

export default GithubButton;
