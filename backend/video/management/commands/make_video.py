"""
Video Factory Management Command
--------------------------------
The Master Orchestrator for the AI Video Factory.

Usage:
    python manage.py make_video --input="my_video.mp4"
    python manage.py make_video --input="my_video.mp4" --mock  # Use mock data (no API calls)
    python manage.py make_video --input="my_video.mp4" --api   # Use OpenAI API for transcription
"""

import os
import json
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from video.ai_services import (
    TranscriptionService, 
    VisualMappingService, 
    ImageGenerationService
)
from video.utils import (
    get_media_paths,
    get_video_metadata,
    generate_render_props,
    ensure_symlink,
    validate_video_file
)


class Command(BaseCommand):
    help = 'Orchestrate the AI Video Factory - Transform raw footage into high-retention vertical videos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--input', 
            type=str, 
            required=True, 
            help='Filename in media/raw/ directory'
        )
        parser.add_argument(
            '--mock',
            action='store_true',
            help='Use mock data instead of AI services (for testing)'
        )
        parser.add_argument(
            '--api',
            action='store_true',
            help='Use OpenAI API for transcription (instead of local Whisper)'
        )
        parser.add_argument(
            '--style',
            type=str,
            default='modern, cinematic, vibrant',
            help='Style hint for visual generation'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image generation (use placeholder visuals)'
        )
        parser.add_argument(
            '--skip-render',
            action='store_true',
            help='Skip the final render step (just generate props)'
        )
    
    def handle(self, *args, **options):
        filename = options['input']
        use_mock = options['mock']
        use_api = options['api']
        style_hint = options['style']
        skip_images = options['skip_images']
        skip_render = options['skip_render']
        
        # Setup paths
        paths = get_media_paths()
        raw_path = paths['raw'] / filename
        
        self.stdout.write(
            self.style.WARNING(f"🚀 Starting AI Video Factory Pipeline")
        )
        self.stdout.write(f"   Input: {filename}")
        self.stdout.write(f"   Mode: {'Mock' if use_mock else 'Production'}")
        
        # ========================================
        # STEP 0: Validation
        # ========================================
        self.stdout.write(self.style.NOTICE("\n📋 Step 0: Validating input..."))
        
        is_valid, error = validate_video_file(str(raw_path))
        if not is_valid:
            raise CommandError(f"Invalid video file: {error}")
        
        # Get video metadata
        try:
            metadata = get_video_metadata(str(raw_path))
            self.stdout.write(
                f"   ✅ Video validated: {metadata['duration']:.1f}s, "
                f"{metadata['width']}x{metadata['height']} @ {metadata['fps']:.0f}fps"
            )
        except Exception as e:
            raise CommandError(f"Failed to read video metadata: {e}")
        
        # ========================================
        # STEP 1: Transcription
        # ========================================
        self.stdout.write(self.style.NOTICE("\n🎤 Step 1: Transcribing audio..."))
        
        if use_mock:
            transcript_data = self._get_mock_transcript()
            self.stdout.write("   ✅ Using mock transcript data")
        else:
            try:
                service = TranscriptionService(model_name="base")
                transcript_data = service.transcribe(str(raw_path), use_api=use_api)
                self.stdout.write(
                    f"   ✅ Transcribed {len(transcript_data)} segments"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️ Transcription failed: {e}")
                )
                self.stdout.write("   Falling back to mock data...")
                transcript_data = self._get_mock_transcript()
        
        # Print transcript preview
        for i, seg in enumerate(transcript_data[:3]):
            self.stdout.write(
                f"   [{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text'][:50]}..."
            )
        if len(transcript_data) > 3:
            self.stdout.write(f"   ... and {len(transcript_data) - 3} more segments")
        
        # ========================================
        # STEP 2: Visual Mapping (LLM)
        # ========================================
        self.stdout.write(self.style.NOTICE("\n🎨 Step 2: Generating visual prompts..."))
        
        if use_mock:
            visual_prompts = self._get_mock_visual_prompts()
            self.stdout.write("   ✅ Using mock visual prompts")
        else:
            try:
                mapper = VisualMappingService()
                visual_prompts = mapper.generate_visual_prompts(
                    transcript_data, 
                    style_hint=style_hint
                )
                self.stdout.write(
                    f"   ✅ Generated {len(visual_prompts)} visual prompts"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️ Visual mapping failed: {e}")
                )
                self.stdout.write("   Falling back to mock data...")
                visual_prompts = self._get_mock_visual_prompts()
        
        # ========================================
        # STEP 3: Asset Generation
        # ========================================
        self.stdout.write(self.style.NOTICE("\n🖼️ Step 3: Generating visual assets..."))
        
        if skip_images or use_mock:
            visuals = self._get_mock_visuals()
            self.stdout.write("   ✅ Using placeholder visuals")
        else:
            try:
                generator = ImageGenerationService(provider="dalle")
                visuals = generator.generate_batch(
                    visual_prompts, 
                    str(paths['assets'])
                )
                self.stdout.write(
                    f"   ✅ Generated {len(visuals)} images"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️ Image generation failed: {e}")
                )
                self.stdout.write("   Falling back to placeholder visuals...")
                visuals = self._get_mock_visuals()
        
        # ========================================
        # STEP 4: Props Injection
        # ========================================
        self.stdout.write(self.style.NOTICE("\n📝 Step 4: Preparing Remotion props..."))
        
        # Ensure symlink exists
        ensure_symlink()
        
        props_path = generate_render_props(
            video_filename=filename,
            transcript=transcript_data,
            visuals=visuals
        )
        self.stdout.write(f"   ✅ Props written to: {props_path}")
        
        if skip_render:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Pipeline complete (render skipped)")
            )
            return
        
        # ========================================
        # STEP 5: Remotion Render
        # ========================================
        self.stdout.write(self.style.NOTICE("\n🎬 Step 5: Rendering with Remotion..."))
        
        output_filename = f"final_{Path(filename).stem}.mp4"
        output_path = paths['output'] / output_filename
        
        # Calculate duration in frames
        duration_frames = int(metadata['duration'] * 30)  # 30 fps
        
        cmd = [
            "npx", "remotion", "render",
            "SplitScreen",
            str(output_path),
            f"--props={props_path}",
            f"--frames=0-{duration_frames}"
        ]
        
        self.stdout.write(f"   Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(settings.PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=True
            )
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Video rendered successfully!")
            )
            self.stdout.write(f"   Output: {output_path}")
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Render failed!"))
            self.stdout.write(f"   Error: {e.stderr}")
            raise CommandError("Remotion render failed")
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR("\n❌ Remotion CLI not found!")
            )
            self.stdout.write("   Run: npm install")
            raise CommandError("Remotion not installed")
    
    def _get_mock_transcript(self):
        """Return mock transcript data for testing."""
        return [
            {"start": 0, "end": 3, "text": "AI Automation is the future of content creation."},
            {"start": 3, "end": 6, "text": "We use Django to orchestrate everything seamlessly."},
            {"start": 6, "end": 10, "text": "And Remotion renders beautiful pixels at scale."},
            {"start": 10, "end": 14, "text": "The result is professional video content in minutes."},
        ]
    
    def _get_mock_visual_prompts(self):
        """Return mock visual prompts for testing."""
        return [
            {
                "time": 0,
                "prompt": "Futuristic AI robot working on creative content, neon lights, cyberpunk style",
                "duration": 4
            },
            {
                "time": 4,
                "prompt": "Clean modern server room with glowing Django logo, minimalist tech aesthetic",
                "duration": 4
            },
            {
                "time": 8,
                "prompt": "Abstract visualization of video rendering, colorful pixels flowing, cinematic",
                "duration": 6
            },
        ]
    
    def _get_mock_visuals(self):
        """Return mock visual paths for testing."""
        return [
            {"start": 0, "src": "/media/assets/placeholder_1.jpg"},
            {"start": 4, "src": "/media/assets/placeholder_2.jpg"},
            {"start": 8, "src": "/media/assets/placeholder_3.jpg"},
        ]
