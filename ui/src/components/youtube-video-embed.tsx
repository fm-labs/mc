
interface YoutubeVideoProps {
    videoId: string;
    title?: string;
    controls?: boolean;
    width?: number;
    height?: number;
    allowFullScreen?: boolean;
}

function YoutubeVideoEmbed(props: YoutubeVideoProps) {
    const defaultIframeProps = {
        width: 560,
        height: 315,
        //title: "YouTube video player",
        frameBorder: 0,
        allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
        allowFullScreen: true,
    };

    const buildIframeProps = () => {
        const { videoId, controls, ...iframeProps } = props;
        let src = `https://www.youtube-nocookie.com/embed/${videoId}`;
        if (!controls) {
            src += "?controls=0";
        }
        return { ...defaultIframeProps, ...iframeProps, src: src };
    };

    return (
        <>
            <iframe title={"YouTube video player"} {...buildIframeProps()}>
                Sorry, your browser does not support iframes.
            </iframe>
        </>
    );
}

export default YoutubeVideoEmbed;
