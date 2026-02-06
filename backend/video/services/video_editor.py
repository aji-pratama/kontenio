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
        print(f"DEBUG: Processing {len(segments)} segments. Total Duration: {total_duration}")
        background = ColorClip(size=(self.width, self.height), color=(10, 10, 10)).with_duration(total_duration)

        clips = []
        subtitle_clips = []

        for segment in segments:
            print(f"DEBUG: Segment {segment.order} | {segment.start_time}-{segment.end_time}")
            start = max(0, segment.start_time)
            end = min(total_duration, segment.end_time)
            duration = end - start
            if duration <= 0: 
                print(f"DEBUG: Skipping segment due to duration {duration}")
                continue

            # --- A. Layer Logic (Primary & Secondary) ---
            print(f"DEBUG: Processing Clip Layout: {segment.layout_event}")

            # --- A. Layer Logic (Primary & Secondary) ---
            
            # Secondary Asset (Top)
            asset_path = segment.asset_file.path if segment.asset_file else None
            if asset_path and os.path.exists(asset_path):
                # Check if video or image
                if asset_path.lower().endswith(('.mp4', '.mov', '.avi')):
                    secondary_clip = VideoFileClip(asset_path).subclipped(0, min(duration, 10)).resized(width=self.width)
                else:
                    secondary_clip = ImageClip(asset_path).with_duration(duration)
                    
                    # PRD: Ken Burns Effect (Slow zoom 1.0x -> 1.1x)
                    if segment.animation_type == 'ken_burns':
                        # v2 transformation
                        secondary_clip = secondary_clip.resized(lambda t: 1.0 + 0.1 * (t / duration))
            else:
                secondary_clip = ColorClip(size=(self.width, 960), color=(20, 20, 20)).with_duration(duration)

            # Layout Switch
            if segment.layout_event == 'bottom_full':
                # Full screen primary
                seg_primary = primary_video.subclipped(start, end).resized(height=self.height).with_position('center')
                clips.append(seg_primary.with_start(start))
            
            elif segment.layout_event == 'top_full':
                # Full screen secondary
                seg_secondary = secondary_clip.resized(width=self.width).with_position('center')
                clips.append(seg_secondary.with_start(start))
            
            else: # Standard Split (50/50)
                # Primary (Bottom) - Center Cropped to fit 1080x960
                # We want the 'middle' of the source video, not the top ceiling.
                # Assuming source is 9:16, we take the center 960px height.

                # Check source dimensions to avoid errors
                src_h = primary_video.h
                crop_y_center = src_h / 2

                # Create the bottom clip
                seg_primary = (primary_video.subclipped(start, end)
                               .cropped(width=self.width, height=960, x_center=self.width/2, y_center=crop_y_center)
                               .with_position(('center', 960)))

                # Secondary (Top)
                seg_secondary = secondary_clip.resized(width=self.width).with_position(('center', 0))
                
                clips.append(seg_secondary.with_start(start))
                clips.append(seg_primary.with_start(start))

            # --- B. Subtitle Logic (Apple Glass Aesthetic) ---
            if segment.transcript:
                text = segment.transcript.upper()
                
                try:
                    # Typography Settings
                    font_size = 42
                    box_width = 840
                    
                    # Shadow Text (Timbul)
                    shadow_clip = TextClip(
                        text=text, 
                        font_size=font_size, 
                        color='black', 
                        method='caption', 
                        size=(box_width, None),
                        text_align='center'
                    ).with_start(start).with_duration(duration).with_position(('center', 960 + 2)).with_opacity(0.6)
                    
                    # Main Text
                    txt_clip = TextClip(
                        text=text, 
                        font_size=font_size, 
                        color='white', 
                        font='Helvetica-Bold', # Try a cleaner font if available, else default
                        method='caption', 
                        size=(box_width, None),
                        text_align='center'
                    ).with_start(start).with_duration(duration).with_position(('center', 960))
                    
                    subtitle_clips.extend([shadow_clip, txt_clip])
                except Exception as e:
                    print(f"Warning: TextClip failed: {e}")

        # 3. Dynamic Glass Box Overlay (Apple Glass)
        # Replaced static box with a cleaner look
        # Box should be centered at the split line or where text is?
        # Text is at ('center', 960) -> Middle of screen (split line).
        # We want the box to cover the text area. 
        # Let's make a box of height 300px centered at 960.
        
        box_h = 300
        box_y = 960 - (box_h / 2)
        
        # Glass Background (White translucent)
        glass_bg = ColorClip(size=(900, box_h), color=(255, 255, 255)) \
            .with_opacity(0.15) \
            .with_position(('center', 960 - (box_h/2))) \
            .with_duration(total_duration)

        # Top Border (Thin White Line)
        border_top = ColorClip(size=(900, 2), color=(255, 255, 255)) \
            .with_opacity(0.6) \
            .with_position(('center', box_y)) \
            .with_duration(total_duration)
            
        # Bottom Border
        border_bottom = ColorClip(size=(900, 2), color=(255, 255, 255)) \
            .with_opacity(0.6) \
            .with_position(('center', box_y + box_h)) \
            .with_duration(total_duration)
            
        # 4. Final Composition
        # Order: Background -> Video/Images -> Glass Box -> Text
        final_video = CompositeVideoClip(
            [background] + clips + 
            [glass_bg, border_top, border_bottom] + 
            subtitle_clips
        )

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
