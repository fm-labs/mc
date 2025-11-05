// Mermaid.tsx
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

type Props = {
    chart: string;                 // the raw mermaid code
    theme?: "default" | "dark" | "forest" | "neutral";
};

export default function Mermaid({ chart, theme = "default" }: Props) {
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        let cancelled = false;

        // Safe initialize on the client
        mermaid.initialize({
            startOnLoad: false,
            securityLevel: "strict",    // or "loose" if you embed HTML in labels
            theme,
        });

        (async () => {
            try {
                // mermaid.render returns { svg, bindFunctions }
                const { svg } = await mermaid.render(
                    // unique id per render
                    `mmd-${Math.random().toString(36).slice(2)}`,
                    chart
                );
                if (!cancelled && ref.current) {
                    ref.current.innerHTML = svg;
                }
            } catch (e) {
                if (ref.current) {
                    ref.current.innerHTML = `<pre style="color:#c00;white-space:pre-wrap;">${String(e)}</pre>`;
                }
            }
        })();

        return () => { cancelled = true; };
    }, [chart, theme]);

    return <div ref={ref} aria-label="Mermaid diagram" />;
}
