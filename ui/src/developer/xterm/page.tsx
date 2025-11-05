import XtermComponent from "@/developer/xterm/components/xterm-component.tsx";
import MainContent from "@/components/layout/main-content.tsx";

const XtermPage = () => {

    const handleData = async (data: string) => {
        console.log('Terminal data:', data, parseInt(data.charAt(0)));
    }

    const handleSubmit = async (command: string) => {
        console.log('Command submitted:', command);
    }


    return (
        <MainContent>
            <h1>Xterm.js Integration</h1>
            <XtermComponent
                //ref={terminalRef}
                onSubmit={handleSubmit}
                onData={handleData}
                style={{ height: '500px', border: '1px solid #ccc' }}
            />
        </MainContent>
    );
};

export default XtermPage;
