import React, { useRef, useState, useCallback } from 'react';
import XtermComponent from "@/developer/xterm/components/xterm-component.tsx";

const ShellSimulator = () => {
    const terminalRef = useRef<any>(null);
    const [currentLine, setCurrentLine] = useState('');
    const [_commandHistory, setCommandHistory] = useState<any[]>([]);
    const [_historyIndex, setHistoryIndex] = useState(-1);

    const prompt = 'user@localhost:~$ ';

    // Simulate shell commands
    const executeCommand = useCallback((command: string) => {
        const cmd = command.trim().toLowerCase();
        let output = '';

        switch (cmd) {
            case '':
                break;
            case 'help':
                output = 'Available commands: help, clear, ls, pwd, date, echo [text], whoami\r\n';
                break;
            case 'clear':
                if (terminalRef.current) {
                    terminalRef.current.clear();
                }
                return;
            case 'ls':
                output = 'Documents  Downloads  Pictures  Music  Videos  Desktop\r\n';
                break;
            case 'pwd':
                output = '/home/user\r\n';
                break;
            case 'date':
                output = new Date().toString() + '\r\n';
                break;
            case 'whoami':
                output = 'user\r\n';
                break;
            default:
                if (cmd.startsWith('echo ')) {
                    output = cmd.substring(5) + '\r\n';
                } else {
                    output = `Command not found: ${cmd}\r\n`;
                }
        }

        if (terminalRef.current && output) {
            terminalRef.current.write(output);
        }

        // Add to history
        if (command.trim()) {
            setCommandHistory(prev => [...prev, command.trim()]);
            setHistoryIndex(-1);
        }
    }, []);

    const handleData = useCallback(async (data: string) => {
        const code = data.charCodeAt(0);

        if (code === 13) { // Enter
            terminalRef.current.write('\r\n');
            executeCommand(currentLine);
            setCurrentLine('');
            terminalRef.current.write(prompt);
        } else if (code === 127) { // Backspace
            if (currentLine.length > 0) {
                setCurrentLine(prev => prev.slice(0, -1));
                terminalRef.current.write('\b \b');
            }
        } else if (code === 27) { // Escape sequences (arrow keys)
            // Handle arrow keys for command history
            // This is a simplified version - full implementation would need more complex parsing
        } else if (code >= 32 && code <= 126) { // Printable characters
            setCurrentLine(prev => prev + data);
            terminalRef.current.write(data);
        }
    }, [currentLine, executeCommand]);

    React.useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.write('Welcome to Shell Simulator!\r\n');
            terminalRef.current.write('Type "help" for available commands.\r\n');
            terminalRef.current.write(prompt);
        }
    }, []);

    return (
        <div style={{ padding: '20px' }}>
            <h2>xterm.js Shell Simulator</h2>
            <XtermComponent
                //ref={terminalRef}
                onData={handleData}
                style={{ height: '500px', border: '1px solid #ccc' }}
            />
        </div>
    );
};

export default ShellSimulator;
