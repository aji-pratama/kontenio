import "./index.css";
import { Composition, staticFile } from "remotion";
import { SplitScreen, type SplitScreenProps } from "./compositions/SplitScreen";

export const RemotionRoot: React.FC = () => {
  // Default props for preview in Remotion Studio
  const defaultProps: SplitScreenProps = {
    videoUrl: staticFile("media/raw/sample.mp4"),
    transcript: [
      { start: 0, end: 3, text: "AI Automation is the future of content creation." },
      { start: 3, end: 6, text: "We use Django to orchestrate everything seamlessly." },
      { start: 6, end: 10, text: "And Remotion renders beautiful pixels at scale." },
    ],
    visuals: [
      { start: 0, src: staticFile("media/assets/placeholder_1.jpg") },
      { start: 4, src: staticFile("media/assets/placeholder_2.jpg") },
    ],
  };

  return (
    <>
      {/* Main Split Screen Composition - Vertical 9:16 Format */}
      <Composition
        id="SplitScreen"
        component={SplitScreen}
        durationInFrames={300} // Default duration, will be overridden by calculateMetadata
        calculateMetadata={async ({ props }) => {
          if (props.transcript && props.transcript.length > 0) {
            const lastSeg = props.transcript[props.transcript.length - 1];
            return {
              durationInFrames: Math.ceil((lastSeg.end + 2) * 30),
            };
          }
          return { durationInFrames: 300 };
        }}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />

      {/* Preview composition with shorter duration */}
      <Composition
        id="SplitScreenPreview"
        component={SplitScreen}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
    </>
  );
};
