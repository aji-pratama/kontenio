import React from 'react';
import {
    AbsoluteFill,
    Video,
    Img,
    useCurrentFrame,
    useVideoConfig,
    interpolate
} from 'remotion';

// ============================================
// TYPE DEFINITIONS
// ============================================

type TranscriptSegment = {
    start: number;
    end: number;
    text: string;
};

type Visual = {
    start: number;
    src: string;
};

export type SplitScreenProps = {
    videoUrl: string;
    transcript: TranscriptSegment[];
    visuals: Visual[];
};

// ============================================
// GLASSMORPHISM STYLES
// ============================================

const glassStyles: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 10,
    width: '85%',
    padding: '40px',
    textAlign: 'center',

    // GLASSMORPHISM MAGIC
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    borderRadius: '30px',
    border: '1px solid rgba(255, 255, 255, 0.25)',
    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
};

const textStyles: React.CSSProperties = {
    color: 'white',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    fontWeight: 800,
    fontSize: '50px',
    margin: 0,
    lineHeight: 1.2,
    textShadow: '0 2px 10px rgba(0,0,0,0.5)',
    letterSpacing: '-0.02em',
};

// ============================================
// HELPER COMPONENTS
// ============================================

interface AnimatedTextProps {
    text: string;
    frame: number;
    fps: number;
}

const AnimatedText: React.FC<AnimatedTextProps> = ({ text, frame, fps }) => {
    const opacity = interpolate(
        frame % (fps * 3),
        [0, fps * 0.5],
        [0.7, 1],
        { extrapolateRight: 'clamp' }
    );

    const scale = interpolate(
        frame % (fps * 3),
        [0, fps * 0.3],
        [0.98, 1],
        { extrapolateRight: 'clamp' }
    );

    return (
        <h1
            style={{
                ...textStyles,
                opacity,
                transform: `scale(${scale})`,
            }}
        >
            {text}
        </h1>
    );
};

interface VisualPanelProps {
    src: string | null;
    frame: number;
    fps: number;
}

const VisualPanel: React.FC<VisualPanelProps> = ({ src, frame, fps }) => {
    if (!src) {
        return (
            <div
                style={{
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
                }}
            />
        );
    }

    const scale = interpolate(
        frame,
        [0, fps * 10],
        [1, 1.15],
        { extrapolateRight: 'extend' }
    );

    return (
        <Img
            src={src}
            style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: `scale(${scale})`,
            }}
        />
    );
};

// ============================================
// MAIN COMPOSITION
// ============================================

export const SplitScreen: React.FC<SplitScreenProps> = ({
    videoUrl,
    transcript,
    visuals
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const currentTime = frame / fps;

    const activeSegment = transcript.find(
        (seg) => currentTime >= seg.start && currentTime < seg.end
    );

    const activeVisual = visuals
        .filter((vis) => currentTime >= vis.start)
        .slice(-1)[0];

    const separatorOpacity = interpolate(
        frame,
        [0, fps * 0.5],
        [0, 0.5],
        { extrapolateRight: 'clamp' }
    );

    return (
        <AbsoluteFill style={{ backgroundColor: '#000' }}>

            {/* --- SPLIT 1: TOP (Visuals) - 50% --- */}
            <div
                style={{
                    position: 'absolute',
                    top: 0,
                    width: '100%',
                    height: '50%',
                    overflow: 'hidden'
                }}
            >
                <VisualPanel
                    src={activeVisual?.src || null}
                    frame={frame}
                    fps={fps}
                />

                <div
                    style={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: '30%',
                        background: 'linear-gradient(to bottom, transparent, rgba(0,0,0,0.3))',
                        pointerEvents: 'none',
                    }}
                />
            </div>

            {/* --- SPLIT 2: BOTTOM (Talking Head) - 50% --- */}
            <div
                style={{
                    position: 'absolute',
                    bottom: 0,
                    width: '100%',
                    height: '50%',
                    overflow: 'hidden'
                }}
            >
                <Video
                    src={videoUrl}
                    style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                    }}
                />

                <div
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '30%',
                        background: 'linear-gradient(to top, transparent, rgba(0,0,0,0.3))',
                        pointerEvents: 'none',
                    }}
                />
            </div>

            {/* --- SEPARATOR LINE --- */}
            <div
                style={{
                    position: 'absolute',
                    top: '50%',
                    left: '5%',
                    right: '5%',
                    height: '2px',
                    background: `linear-gradient(90deg, transparent 0%, rgba(255,255,255,${separatorOpacity}) 20%, rgba(255,255,255,${separatorOpacity}) 80%, transparent 100%)`,
                    zIndex: 5,
                }}
            />

            {/* --- LAYER 3: GLASSY TEXT OVERLAY --- */}
            {activeSegment && (
                <div style={glassStyles}>
                    <AnimatedText
                        text={activeSegment.text}
                        frame={frame}
                        fps={fps}
                    />
                </div>
            )}

        </AbsoluteFill>
    );
};

export default SplitScreen;
