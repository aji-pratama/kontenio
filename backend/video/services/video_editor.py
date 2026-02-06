import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw
from django.conf import settings
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
from moviepy.video import fx as vfx

def create_rounded_mask(size, radius):
    """Create a rounded rectangle mask using PIL."""
    w, h = size
    # Create high-res image for anti-aliasing
    factor = 4
    img = Image.new('L', (w * factor, h * factor), 0)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, w * factor, h * factor), radius * factor, fill=255)
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    return ImageClip(np.array(img) / 255.0).with_is_mask(True)


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

        for i, segment in enumerate(segments):
            print(f"DEBUG: Segment {segment.order} | {segment.start_time}-{segment.end_time}")
            start = max(0, segment.start_time)
            end = min(total_duration, segment.end_time)
            duration = end - start
            if duration <= 0: 
                print(f"DEBUG: Skipping segment due to duration {duration}")
                continue

            # --- A. Layer Logic (Primary & Secondary) ---
            print(f"DEBUG: Processing Clip Layout: {segment.layout_event}")
            
            # Secondary Asset (Top)
            asset_path = segment.asset_file.path if segment.asset_file else None
            asset_exists = asset_path and os.path.exists(asset_path)
            
            if asset_exists:
                if asset_path.lower().endswith(('.mp4', '.mov', '.avi')):
                    secondary_clip = VideoFileClip(asset_path).subclipped(0, min(duration, 10)).resized(width=self.width)
                else:
                    secondary_clip = ImageClip(asset_path).with_duration(duration)
                    if segment.animation_type == 'ken_burns':
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
            
            else: # Standard Split (Card Style Aesthetic)
                # Specs for "Floating Cards"
                card_w, card_h, card_r = 1040, 920, 40
                
                # Primary (Bottom Card)
                # 1. Resized to fit container width
                seg_primary = primary_video.subclipped(start, end)
                if seg_primary.w != self.width: 
                    seg_primary = seg_primary.resized(width=self.width)
                
                # 2. Crop to Card Size
                seg_primary = seg_primary.cropped(
                    width=card_w, height=card_h, 
                    x_center=self.width/2, y_center=seg_primary.h/2
                ).with_position(('center', 980)) # Just below center line
                
                # 3. Apply Rounded Mask
                seg_primary = seg_primary.with_mask(create_rounded_mask((card_w, card_h), card_r))

                # Secondary (Top Card)
                # 1. Resize
                seg_secondary = secondary_clip.resized(width=self.width)
                
                # 2. Crop to Card Size
                seg_secondary = seg_secondary.cropped(
                    width=card_w, height=card_h, 
                    x_center=self.width/2, y_center=seg_secondary.h/2
                ).with_position(('center', 20)) # Just above center line
                
                # 3. Apply Rounded Mask
                seg_secondary = seg_secondary.with_mask(create_rounded_mask((card_w, card_h), card_r))
                
                clips.append(seg_secondary.with_start(start))
                clips.append(seg_primary.with_start(start))

            # --- B. Subtitle Logic (Apple Glass Aesthetic) ---
            if segment.transcript:
                text = segment.transcript.upper()
                
                try:
                    # Typography Settings
                    font_size = 36 # Reduced font size
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
                        # font='Helvetica-Bold', 
                        method='caption', 
                        size=(box_width, None),
                        text_align='center'
                    ).with_start(start).with_duration(duration).with_position(('center', 960))
                    
                    subtitle_clips.extend([shadow_clip, txt_clip])
                except Exception as e:
                    print(f"Warning: TextClip failed: {e}")

        # 3. Dynamic Glass Box Overlay (Apple Glass)
        # Specs: Rounded, 0.15 opacity, 1px border 0.3 opacity.
        box_w, box_h = 900, 320 # Increased Height
        radius = 30
        
        def create_glass_panel(w, h, r):
            # Create PIL image with white border and semi-transparent fill
            factor = 4
            img = Image.new('RGBA', (w*factor, h*factor), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            
            # Fill (White 15%) -> (255, 255, 255, 38)
            draw.rounded_rectangle((0, 0, w*factor, h*factor), r*factor, fill=(255,255,255,38))
            
            # Border (White 40%, 1px -> 4px at 4x) -> (255, 255, 255, 100)
            draw.rounded_rectangle((0, 0, w*factor, h*factor), r*factor, outline=(255,255,255,100), width=4)
            
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            return img

        glass_img = create_glass_panel(box_w, box_h, radius)
        glass_box = ImageClip(np.array(glass_img)) \
            .with_position(('center', 960 - (box_h/2))) \
            .with_duration(total_duration)
            
        # 4. Final Composition
        final_video = CompositeVideoClip(
            [background] + clips + 
            [glass_box] + 
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
