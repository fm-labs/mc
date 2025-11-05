import React, { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { Button } from "@/components/ui/button.tsx";
import 'xterm/css/xterm.css';

interface XtermComponentProps {
    onData?: (data: string) => Promise<void>;
    onSubmit?: (command: string) => Promise<void>;
    options?: any;
    className?: string;
    style?: React.CSSProperties;
}

const XtermComponent = ({
                            onData,
                            onSubmit,
                            options = {},
                            className = '',
                            style = {}
                        }: XtermComponentProps) => {
    const terminalRef = useRef<any>(null);
    const terminal = useRef<Terminal>(null);
    const fitAddon = useRef<FitAddon>(null);
    const inputBufferRef = useRef<string>('');

    const handleData = (data: string) => {
        if (terminal.current) {
            // check if CTRL+C is pressed
            if (data.charCodeAt(0) === 3) { // Ctrl+C
                terminal.current.write('^C\r\n$ ');
                inputBufferRef.current = '';
                return;
            } else if (data.charCodeAt(0) === 4) { // Ctrl+D
                terminal.current.write('^D\r\n');
                if (onSubmit) {
                    onSubmit('exit');
                }
                inputBufferRef.current = '';
                return;
            } else if (data.charCodeAt(0) === 13) { // Enter key
                terminal.current.write('\r\n$ ');
                const command = inputBufferRef.current.trim();
                if (command.length === 0) {
                    inputBufferRef.current = '';
                    return;
                }
                console.log("Command entered:", command);
                if (command === 'clear') {
                    terminal.current.clear();
                    inputBufferRef.current = '';
                    return;
                }

                if (onSubmit) {
                    onSubmit(command);
                }
                inputBufferRef.current = '';
            } else if (data.charCodeAt(0) === 127) { // Backspace key
                console.log("Backspace pressed, current buffer:", inputBufferRef.current);
                if (inputBufferRef.current.length > 0) {
                    terminal.current.write('\b \b');
                    inputBufferRef.current = inputBufferRef.current.slice(0, -1);
                }
            } else {
                terminal.current.write(data);
                inputBufferRef.current += data;
            }
        }
        if (onData) {
            onData(data);
        }
    }

    useEffect(() => {
        if (!terminalRef.current) {
            console.warn("Terminal container not ready yet");
            return;
        }
        // Initialize terminal
        inputBufferRef.current = '';
        terminal.current = new Terminal({
            cursorBlink: true,
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace',
            fontSize: 14,
            theme: {
                background: '#1e1e1e',
                foreground: '#ffffff',
                cursor: '#ffffff',
                //selection: '#ffffff40',
                black: '#000000',
                red: '#e06c75',
                green: '#98c379',
                yellow: '#d19a66',
                blue: '#61afef',
                magenta: '#c678dd',
                cyan: '#56b6c2',
                white: '#abb2bf',
                brightBlack: '#5c6370',
                brightRed: '#e06c75',
                brightGreen: '#98c379',
                brightYellow: '#d19a66',
                brightBlue: '#61afef',
                brightMagenta: '#c678dd',
                brightCyan: '#56b6c2',
                brightWhite: '#ffffff'
            },
            ...options
        });

        // Initialize addons
        fitAddon.current = new FitAddon();
        const webLinksAddon = new WebLinksAddon();

        // Load addons
        terminal.current.loadAddon(fitAddon.current);
        terminal.current.loadAddon(webLinksAddon);

        // Open terminal in the container
        //terminal.current.open(terminalRef.current);

        // Fit terminal to container
        //fitAddon.current.fit();

        // Handle data input from terminal
        terminal.current.onData(handleData)

        terminal.current.write('$ ');

        // Handle resize
        const handleResize = () => {
            if (fitAddon.current) {
                fitAddon.current.fit();
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (terminal.current) {
                terminal.current.dispose();
            }
        };
    }, []);

    // // Expose terminal methods
    // const writeToTerminal = (data: any) => {
    //     if (terminal.current) {
    //         terminal.current.write(data);
    //     }
    // };
    //
    // const clearTerminal = () => {
    //     if (terminal.current) {
    //         terminal.current.clear();
    //     }
    // };
    //
    // const focusTerminal = () => {
    //     if (terminal.current) {
    //         terminal.current.focus();
    //     }
    // };
    //
    // // Expose methods to parent component
    // React.useImperativeHandle(terminalRef, () => ({
    //     write: writeToTerminal,
    //     clear: clearTerminal,
    //     focus: focusTerminal,
    //     terminal: terminal.current
    // }));

    return (
        <div>
            <div>
                <Button onClick={() => {
                    if (terminalRef.current && terminal.current) {
                        const el = document.getElementById('xterm-container');
                        if (el) {
                            el.innerHTML = ''; // Clear previous terminal content
                            terminal.current.open(el);
                            if (fitAddon.current) {
                                fitAddon.current.fit();
                            }
                            terminal.current.focus();
                        }
                    } else {
                        console.warn("Terminal or container not ready yet");
                    }
                }}>Open Terminal</Button>
                <Button onClick={() => {
                    // if (terminalRef.current) {
                    //     terminalRef.current.clear();
                    //     terminalRef.current.write('Terminal cleared!\r\n');
                    // }
                    console.log("Clearing terminal", terminal.current);
                    if (terminal.current) {
                        terminal.current.clear();
                        // Reset input buffer
                        inputBufferRef.current = '';
                    }
                }}>Clear Terminal</Button>
            </div>
            <hr />
            Buffer Content: {inputBufferRef.current}
            <hr />
            <div
                id={"xterm-container"}
                ref={terminalRef}
                className={className}
                style={{
                    width: '100%',
                    height: '400px',
                    ...style
                }}
            />
        </div>
    );
};

export default XtermComponent;
