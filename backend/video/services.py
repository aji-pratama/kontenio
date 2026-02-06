"""
Video Processing Service
------------------------
Integrates AI services with Django models for admin-triggered processing.
"""

import os
import json
import subprocess
from pathlib import Path
from django.conf import settings

from .models import VideoProject, VisualAsset
from .ai_services import (
    TranscriptionService, 
    VisualMappingService, 
    ImageGenerationService,
    OPENAI_AVAILABLE,
    WHISPER_AVAILABLE
)
from .utils import (
    get_media_paths,
    get_video_metadata,
    generate_render_props,
    ensure_symlink
)


class VideoProcessingService:
    """
    Orchestrates the video processing pipeline for a VideoProject.
    """
    
    def __init__(self, project: VideoProject, use_mock: bool = False):
        self.project = project
        self.use_mock = use_mock
        self.paths = get_media_paths()
    
    def process(self) -> bool:
        """
        Run the complete processing pipeline.
        
        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Step 1: Transcription
            self._transcribe()
            
            # Step 2: Visual Mapping
            self._generate_visual_prompts()
            
            # Step 3: Image Generation
            self._generate_images()
            
            # Step 4: Generate Props
            self._generate_props()
            
            # Step 5: Render
            self._render()
            
            return True
            
        except Exception as e:
            self.project.set_error(str(e))
            return False
    
    def _transcribe(self):
        """Step 1: Transcribe the video."""
        self.project.update_status(
            VideoProject.Status.TRANSCRIBING,
            'Extracting and transcribing audio...'
        )
        
        if self.use_mock:
            transcript = self._get_mock_transcript()
        else:
            video_path = self.project.raw_video.path
            
            try:
                service = TranscriptionService(model_name="base")
                transcript = service.transcribe(
                    video_path, 
                    use_api=self.project.use_api_transcription
                )
            except Exception as e:
                # Fallback to mock on error
                transcript = self._get_mock_transcript()
        
        self.project.transcript_data = transcript
        self.project.save(update_fields=['transcript_data', 'updated_at'])
    
    def _generate_visual_prompts(self):
        """Step 2: Generate visual prompts using GPT-4."""
        self.project.update_status(
            VideoProject.Status.MAPPING,
            'Analyzing transcript and generating visual prompts...'
        )
        
        if self.use_mock or not OPENAI_AVAILABLE:
            prompts = self._get_mock_visual_prompts()
        else:
            try:
                mapper = VisualMappingService()
                prompts = mapper.generate_visual_prompts(
                    self.project.transcript_data,
                    style_hint=self.project.style_hint
                )
            except Exception as e:
                prompts = self._get_mock_visual_prompts()
        
        self.project.visual_prompts_data = prompts
        self.project.save(update_fields=['visual_prompts_data', 'updated_at'])
    
    def _generate_images(self):
        """Step 3: Generate images for each visual prompt."""
        self.project.update_status(
            VideoProject.Status.GENERATING,
            'Generating visual assets...'
        )
        
        visuals = []
        
        if self.use_mock or self.project.skip_image_generation or not OPENAI_AVAILABLE:
            # Use placeholder visuals
            visuals = self._get_mock_visuals()
        else:
            try:
                generator = ImageGenerationService(provider="dalle")
                
                for i, prompt_obj in enumerate(self.project.visual_prompts_data or []):
                    self.project.update_status(
                        VideoProject.Status.GENERATING,
                        f'Generating image {i+1}/{len(self.project.visual_prompts_data)}...'
                    )
                    
                    filename = f"project_{self.project.id}_visual_{i:03d}.jpg"
                    output_path = self.paths['assets'] / filename
                    
                    try:
                        generator.generate(prompt_obj['prompt'], str(output_path))
                        
                        # Create VisualAsset record
                        asset = VisualAsset.objects.create(
                            project=self.project,
                            start_time=prompt_obj['time'],
                            image=f"assets/{filename}",
                            prompt=prompt_obj['prompt'],
                            is_generated=True
                        )
                        
                        visuals.append({
                            'start': prompt_obj['time'],
                            'src': f"/media/assets/{filename}"
                        })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                visuals = self._get_mock_visuals()
        
        self.project.visuals_data = visuals
        self.project.save(update_fields=['visuals_data', 'updated_at'])
    
    def _generate_props(self):
        """Step 4: Generate Remotion props file."""
        self.project.update_status(
            VideoProject.Status.RENDERING,
            'Preparing render configuration...'
        )
        
        # Ensure symlink exists
        ensure_symlink()
        
        # Generate props file
        props_filename = f"props_project_{self.project.id}.json"
        props_path = Path(settings.MEDIA_ROOT) / 'props' / props_filename
        props_path.parent.mkdir(parents=True, exist_ok=True)
        
        generate_render_props(
            video_filename=self.project.raw_video_filename,
            transcript=self.project.transcript_data or [],
            visuals=self.project.visuals_data or [],
            output_path=str(props_path)
        )
        
        # Also generate for Remotion public folder
        public_props_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'
        generate_render_props(
            video_filename=self.project.raw_video_filename,
            transcript=self.project.transcript_data or [],
            visuals=self.project.visuals_data or [],
            output_path=str(public_props_path)
        )
        
        self.project.props_file = f"props/{props_filename}"
        self.project.save(update_fields=['props_file', 'updated_at'])
    
    def _render(self):
        """Step 5: Render the video with Remotion."""
        self.project.update_status(
            VideoProject.Status.RENDERING,
            'Rendering video with Remotion...'
        )
        
        # Get video metadata for duration
        try:
            metadata = get_video_metadata(self.project.raw_video.path)
            duration_frames = int(metadata['duration'] * 30)
        except:
            duration_frames = 300  # Default 10 seconds
        
        output_filename = f"final_project_{self.project.id}.mp4"
        output_path = self.paths['output'] / output_filename
        
        props_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'
        
        cmd = [
            "npx", "remotion", "render",
            "SplitScreen",
            str(output_path),
            f"--props={props_path}",
            f"--frames=0-{duration_frames}"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(settings.PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minute timeout
            )
            
            self.project.output_video = f"output/{output_filename}"
            self.project.update_status(
                VideoProject.Status.COMPLETED,
                'Video rendered successfully!'
            )
            self.project.save(update_fields=['output_video', 'updated_at'])
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Remotion render failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Render timed out after 10 minutes")
        except FileNotFoundError:
            raise RuntimeError("Remotion CLI not found. Run: npm install")
    
    def generate_props_only(self):
        """Generate props without rendering (for preview)."""
        try:
            if not self.project.transcript_data:
                self._transcribe()
            if not self.project.visual_prompts_data:
                self._generate_visual_prompts()
            if not self.project.visuals_data:
                self._generate_images()
            self._generate_props()
            return True
        except Exception as e:
            self.project.set_error(str(e))
            return False
    
    # Mock data methods
    def _get_mock_transcript(self):
        return [
            {"start": 0, "end": 3, "text": "AI Automation is the future of content creation."},
            {"start": 3, "end": 6, "text": "We use Django to orchestrate everything seamlessly."},
            {"start": 6, "end": 10, "text": "And Remotion renders beautiful pixels at scale."},
        ]
    
    def _get_mock_visual_prompts(self):
        return [
            {"time": 0, "prompt": "Futuristic AI robot", "duration": 4},
            {"time": 4, "prompt": "Modern server room", "duration": 4},
            {"time": 8, "prompt": "Video rendering visualization", "duration": 6},
        ]
    
    def _get_mock_visuals(self):
        return [
            {"start": 0, "src": "/media/assets/placeholder_1.jpg"},
            {"start": 4, "src": "/media/assets/placeholder_2.jpg"},
        ]
