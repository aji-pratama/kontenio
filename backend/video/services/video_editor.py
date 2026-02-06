import os
import random
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, ColorClip

class VideoEditorService:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.width = 1080
        self.height = 1920

    def edit_video_v2(self, base_video_path: str, segments: List[Any]):
        """
        Engine Phase 3: Rendering using VideoSegment objects.
        Implements PRD v3 Visual Styles (Apple Glass, Timbul, Ken Burns).
        """
        # 1. Load Primary Video
        primary_video = VideoFileClip(base_video_path)
        total_duration = primary_video.duration

        # 2. Base Background
        background = ColorClip(size=(self.width, self.height), color=(10, 10, 10)).set_duration(total_duration)

        clips = []
        subtitle_clips = []

        for segment in segments:
            start = segment.start_time
            end = segment.end_time
            duration = end - start
            if duration <= 0: continue

            # --- A. Layer Logic (Primary & Secondary) ---
            
            # Secondary Asset (Top)
            asset_path = segment.asset_file.path if segment.asset_file else None
            if asset_path and os.path.exists(asset_path):
                # Check if video or image
                if asset_path.lower().endswith(('.mp4', '.mov', '.avi')):
                    secondary_clip = VideoFileClip(asset_path).subclip(0, min(duration, 10)).resize(width=self.width)
                    # Loop if too short? No, subclip handles it.
                else:
                    secondary_clip = ImageClip(asset_path).set_duration(duration)
                    
                    # PRD: Ken Burns Effect (Slow zoom 1.0x -> 1.1x)
                    if segment.animation_type == 'ken_burns':
                        secondary_clip = secondary_clip.resize(lambda t: 1.0 + 0.1 * (t / duration))
            else:
                secondary_clip = ColorClip(size=(self.width, 960), color=(20, 20, 20)).set_duration(duration)

            # Layout Switch
            if segment.layout_event == 'bottom_full':
                seg_primary = primary_video.subclip(start, end).resize(height=self.height).set_position('center')
                clips.append(seg_primary.set_start(start))
            elif segment.layout_event == 'top_full':
                seg_secondary = secondary_clip.resize(width=self.width).set_position('center')
                clips.append(seg_secondary.set_start(start))
            else: # Standard Split
                seg_primary = primary_video.subclip(start, end).resize(width=self.width).set_position(('center', 960))
                seg_secondary = secondary_clip.resize(width=self.width).set_position(('center', 0))
                clips.append(seg_secondary.set_start(start))
                clips.append(seg_primary.set_start(start))

            # --- B. Subtitle Logic (Apple Glass Aesthetic) ---
            if segment.transcript:
                text = segment.transcript.upper()
                
                try:
                    # Glassmorphism Box (Simulated via high-contrast semi-transparent color)
                    # Note: MoviePy doesn't have native "blur background" filter that works easily on layers,
                    # so we use a semi-transparent white box with a 1px border.
                    
                    # Subtitle Shadow (Timbul look)
                    shadow_offset = 4
                    shadow_clip = TextClip(
                        text, 
                        fontsize=62, 
                        color='black', 
                        font='Arial-Bold', 
                        method='caption', 
                        size=(804, None),
                        print_cmd=False
                    ).set_start(start).set_duration(duration).set_position(('center', 880 + shadow_offset)).set_opacity(0.5)
                    
                    # Main Text
                    txt_clip = TextClip(
                        text, 
                        fontsize=60, 
                        color='white', 
                        font='Arial-Bold', 
                        method='caption', 
                        size=(800, None),
                        print_cmd=False
                    ).set_start(start).set_duration(duration).set_position(('center', 880))
                    
                    subtitle_clips.extend([shadow_clip, txt_clip])
                except Exception as e:
                    print(f"Warning: TextClip failed: {e}")

        # 3. Static Glass Box Overlay (Apple Glass)
        # In PRD, this is a box behind the text. I'll make it static or dynamic per segment?
        # PRD says "Burn-in Apple Glass style text (frosted glass box...)".
        # Let's add a global overlay box for the text area.
        glass_box = ColorClip(size=(900, 220), color=(255, 255, 255)) \
            .set_opacity(0.15) \
            .set_position(('center', 860)) \
            .set_duration(total_duration)
            
        # 4. Final Composition
        final_video = CompositeVideoClip([background] + clips + [glass_box] + subtitle_clips)

        # 5. Export
        final_video.write_videofile(
            self.output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4
        )

        return self.output_path
