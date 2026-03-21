import React from "react";
import {Button} from "@/components/ui/button.tsx";
import {InfoIcon} from "lucide-react";
import {createPortal} from "react-dom";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog.tsx";
import ReactJson from "@microlink/react-json-view";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select.tsx";

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
 * @param asButton
 * @constructor
 */
const Data = ({data, asButton}: { data: any, asButton?: boolean }) => {
    const [showData, setShowData] = React.useState<boolean>(false);
    const toggleShowData = () => setShowData(!showData);
    const [theme, setTheme] = React.useState<string>("chalk");

    return (
        <div className={"inline-block ml-1"}>
            {asButton ? <Button size={"sm"} variant="outline" onClick={toggleShowData} title="Show Data">
                <InfoIcon size={12}/>
            </Button> : <span onClick={toggleShowData} className={"cursor-pointer text-blue-300 underline"}>
                <InfoIcon size={14}/>
            </span>}

            {showData && createPortal(<Dialog open={showData} onOpenChange={() => setShowData(false)}>
                <DialogContent className="sm:max-w-5/6">
                    <div className="w-full">
                        <DialogHeader className="text-start">
                            <DialogTitle>{"Data"}</DialogTitle>
                            <DialogDescription className={"mb-2"}>
                                <Select onValueChange={setTheme}>
                                    <SelectTrigger className="w-[180px]">
                                        <SelectValue placeholder="Theme"/>
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
                                enableClipboard={false}
                                displayObjectSize={false}
                                displayDataTypes={false}/>
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
