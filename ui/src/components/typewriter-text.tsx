import React, { PropsWithChildren, useEffect, useState } from "react";

interface TypewriterTextProps extends PropsWithChildren<any> {
    text: string;
    speed?: number; // Speed in milliseconds per character
    delay?: number; // Initial delay before starting the typing effect
    limit?: number; // Maximum duration for the typing effect
    showCursor?: boolean; // Whether to show the cursor
    cursorChar?: string; // Character for the cursor
    className?: string; // Additional CSS classes
    onComplete?: () => void; // Callback when typing is complete
    children?: React.ReactNode; // Children elements
}

const Cursor = ({ cursorChar = "_", pulse }: { cursorChar: string, pulse?: boolean }) => {
    return <span className={pulse ? "animate-pulse" : ""}>{cursorChar}</span>;
}

const TypewriterText = ({
                            text,
                            speed = 10,
                            delay = 0,
                            limit = 2000,
                            showCursor = true,
                            repeat = false,
                            repeatDelay = 2000,
                            cursorChar = "_",
                            cursorPulse = true,
                            onComplete = () => {
                            },
                            children,
                        }: TypewriterTextProps) => {
    const [displayedText, setDisplayedText] = useState("");
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        setDisplayedText("");
        setCurrentIndex(0);
        setIsComplete(false);
    }, [text]);

    useEffect(() => {
        let timer: any;
        if (currentIndex < text.length) {
            const calculatedDuration = speed * text.length + delay;
            let effectiveSpeed = speed;
            if (limit > 0 && calculatedDuration > limit) {
                effectiveSpeed = Math.min(speed, limit / calculatedDuration * speed);
                console.log(`Adjusted Speed: ${effectiveSpeed}ms for text length: ${text.length}`);
            }
            timer = setTimeout(() => {
                const nextText = text.slice(0, currentIndex + 1);
                setDisplayedText(nextText);
                setCurrentIndex(currentIndex + 1);
            }, currentIndex===0 ? delay : effectiveSpeed);

        } else if (text.length > 0 && currentIndex===text.length && !isComplete) {
            setIsComplete(true);
            onComplete();
        }

        return () => {
            if (timer) {
                clearTimeout(timer);
            }
        }

    }, [currentIndex, text, speed, delay, isComplete, onComplete, repeat, repeatDelay]);

    React.useEffect(() => {
        let repeatTimer: any;
        if (isComplete && repeat) {
            repeatTimer = setTimeout(() => {
                setDisplayedText("");
                setCurrentIndex(0);
                setIsComplete(false);
            }, repeatDelay);
        }

        return () => {
            if (repeatTimer) {
                clearTimeout(repeatTimer);
            }
        }
    }, [isComplete, repeat, repeatDelay]);

    if (isComplete && children) {
        return children;
    }

    return <>
        {displayedText}
        {showCursor && !isComplete && text?.length > 0 ? <Cursor cursorChar={cursorChar} pulse={cursorPulse} /> : ""}
    </>;
};

TypewriterText.Cursor = Cursor;

export default TypewriterText;
