import React from "react";
import MasterPanel from "./master-panel";
import { useMasterContext } from "@/components/master-panel/master-context-provider.tsx";

const MasterPanelInputTab = () => {
    const { addNotification } = useMasterContext();

    const [inputValue, setInputValue] = React.useState("");

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        // check if "enter" key is pressed
        if (e.key==="Enter") {
            console.log("Enter key pressed, input value:", inputValue);
            addNotification("Notification: " + inputValue);
            setInputValue("");
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    };

    return (
        <MasterPanel.Tab>
            <input type={"text"} className={"w-128"} value={inputValue}
                   onKeyDown={handleKeyDown}
                   onChange={handleInputChange}></input>
        </MasterPanel.Tab>
    );
};

export default MasterPanelInputTab;
