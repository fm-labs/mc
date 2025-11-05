import React from "react";
import { Button } from "@/components/ui/button.tsx";
import { InfoIcon } from "lucide-react";
import { createPortal } from "react-dom";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog.tsx";
import ReactJson from "@microlink/react-json-view";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.tsx";

const THEME_KEYS = [
    "apathy", "apathy:inverted", "ashes", "bespin", "brewer",
    "bright:inverted", "bright", "chalk", "codeschool", "colors",
    "eighties", "embers", "flat", "google", "grayscale",
    "grayscale:inverted", "greenscreen", "harmonic", "hopscotch",
    "isotope", "marrakesh", "mocha", "monokai", "ocean",
    "paraiso", "pop", "railscasts", "rjv-default", "shapeshifter",
    "shapeshifter:inverted", "solarized", "summerfruit",
    "summerfruit:inverted", "threezerotwofour", "tomorrow", "tube", "twilight",
];

/**
 * Data Component
 *
 * @param data
 * @constructor
 */
const Data = ({ data, useButton }: { data: any, useButton?: boolean }) => {
    const [showData, setShowData] = React.useState<boolean>(false);
    const toggleShowData = () => setShowData(!showData);
    const [theme, setTheme] = React.useState<string>("chalk");

    return (
        <div className={"inline-block"}>
            {useButton ? <Button size="icon" variant="outline" onClick={toggleShowData} title="Show Data">
                    <InfoIcon />
                </Button> :
                <span onClick={toggleShowData} className={"cursor-pointer text-blue-500 underline"}><InfoIcon size={14} /></span>}
            {showData && createPortal(<Dialog open={showData} onOpenChange={() => setShowData(false)}>
                <DialogContent className="sm:max-w-5/6">
                    <div className="w-full">
                        <DialogHeader className="text-start">
                            <DialogTitle>{"Data"}</DialogTitle>
                            <DialogDescription className={"mb-2"}>
                                <Select onValueChange={setTheme}>
                                    <SelectTrigger className="w-[180px]">
                                        <SelectValue placeholder="Theme" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {THEME_KEYS.map((key) => (
                                            <SelectItem key={key} value={key}>
                                                {key}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </DialogDescription>
                        </DialogHeader>
                        <div className={"max-h-[300px] overflow-y-scroll overflow-scroll"}>
                            {/*<pre className={"text-sm"}>{JSON.stringify(data, null, 2)}</pre>*/}
                            <ReactJson
                                theme={theme as any}
                                src={data}
                                name={false}
                                collapsed={false}
                                enableClipboard={true}
                                displayDataTypes={false} />
                        </div>
                    </div>
                </DialogContent>
                <DialogFooter>

                </DialogFooter>
            </Dialog>, document.getElementById("modal-root")!)}
        </div>
    );
};

export default Data;
