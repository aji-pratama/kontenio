import subprocess, os
from pathlib import Path

from django.conf import settings

from .models import VideoProject, VisualAsset
from .ai_services import (
    ImageGenerationService,
    TranscriptionService,
    VisualMappingService,
)
from .utils import ensure_symlink, generate_render_props, get_media_paths, get_video_metadata


class VideoProcessingService:
    def __init__(self, project: VideoProject):
        self.project = project
        self.paths = get_media_paths()

    def process(self) -> bool:
        try:
            self._transcribe()
            self._generate_visual_prompts()
            self._generate_images()
            self._generate_props()
            self._render()
            return True
        except Exception as e:
            self.project.set_error(str(e))
            return False

    def _transcribe(self):
        provider = self.project.transcription_provider
        provider_display = self.project.get_transcription_provider_display()
        self.project.update_status('transcribing', f'Transcribing with {provider_display}...')

        service = TranscriptionService(provider=provider)
        self.project.transcript_data = service.transcribe(self.project.raw_video.path)
        self.project.save()

    def _generate_visual_prompts(self):
        provider = self.project.llm_provider
        provider_display = self.project.get_llm_provider_display()
        self.project.update_status('mapping', f'Mapping with {provider_display}...')

        mapper = VisualMappingService(provider=provider)
        self.project.visual_prompts_data = mapper.generate_visual_prompts(
            self.project.transcript_data,
            style_hint=self.project.style_hint
        )
        self.project.save()

    def _generate_images(self):
        if self.project.skip_image_generation:
            self.project.visuals_data = []
            self.project.save()
            return

        provider = self.project.image_provider
        provider_display = self.project.get_image_provider_display()
        self.project.update_status('generating', f'Generating images with {provider_display}...')

        generator = ImageGenerationService(provider=provider)

        def progress_callback(current, total):
            self.project.update_status('generating', f'Generating image {current}/{total}...')

        visuals = generator.generate_batch(
            self.project.visual_prompts_data or [],
            str(self.paths['assets']),
            progress_callback=progress_callback
        )

        # Create assets in DB
        prompts_data = self.project.visual_prompts_data or []
        for i, prompt_obj in enumerate(prompts_data):
            # Safety check: ensure prompt_obj is a dictionary
            if not isinstance(prompt_obj, dict):
                continue
                
            if i < len(visuals):
                filename = visuals[i]['src'].split('/')[-1]
                VisualAsset.objects.create(
                    project=self.project,
                    start_time=prompt_obj.get('time', 0),
                    image=f"assets/{filename}",
                    prompt=prompt_obj.get('prompt', ''),
                    is_generated=(provider != 'mock')
                )

        self.project.visuals_data = visuals
        self.project.save()

    def _generate_props(self):
        self.project.update_status('rendering', 'Preparing render...')
        ensure_symlink()

        props_filename = f"props_project_{self.project.id}.json"
        props_path = Path(settings.MEDIA_ROOT) / 'props' / props_filename

        props_args = {
            "video_filename": self.project.raw_video_filename,
            "transcript": self.project.transcript_data or [],
            "visuals": self.project.visuals_data or [],
        }

        generate_render_props(**props_args, output_path=str(props_path))
        
        public_props_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'
        generate_render_props(**props_args, output_path=str(public_props_path))

        self.project.props_file = f"props/{props_filename}"
        self.project.save()

    def _render(self):
        self.project.update_status('rendering', 'Rendering video...')

        metadata = get_video_metadata(self.project.raw_video.path)
        duration_frames = int(metadata.get('duration', 10) * 30)

        output_filename = f"final_{self.project.id}.mp4"
        output_path = self.paths['output'] / output_filename
        # Use the project-specific props file absolute path
        props_path = self.project.props_file.path
        
        # Ensure the shared public path is also updated for local dev visibility
        shared_props_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'
        import shutil
        shutil.copy2(props_path, str(shared_props_path))

        # Remove explicit frame range to let Remotion calculate it automatically via calculateMetadata
        cmd = [
            "npx", "remotion", "render", "SplitScreen",
            str(output_path), f"--props={props_path}",
            "--concurrency=1", 
            "--gl=swiftshader", # Force SwiftShader for stable headless rendering on Mac/Linux
            "--log=verbose",
            "--timeout=120000"
        ]

        # 1. Start dedicated static server for MEDIA_ROOT on port 9005
        # This is the secret sauce for stable local rendering
        media_root = Path(settings.MEDIA_ROOT)
        print("🚀 Starting Dedicated Media Server on :9005...")
        media_server = subprocess.Popen(
            ["python3", "-m", "http.server", "9005", "--directory", str(media_root)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:
            print(f"\n🎥 EXECUTING CMD: {' '.join(cmd)}")
            
            # Inject CHROMIUM_FLAGS (just in case, but http:// bypasses file:// blocks anyway)
            env = os.environ.copy()
            env["CHROMIUM_FLAGS"] = "--disable-web-security --no-sandbox"
            
            # Stream output directly to console
            subprocess.run(cmd, cwd=str(settings.PROJECT_ROOT), check=True, timeout=1200, env=env)
            
            self.project.output_video = f"output/{output_filename}"
            self.project.update_status('completed', 'Rendered successfully!')
            self.project.save()
            
        finally:
            # ALWAYS kill the server
            print("🛑 Stopping Media Server...")
            media_server.terminate()
            media_server.wait()

    def generate_props_only(self):
        try:
            if not self.project.transcript_data: self._transcribe()
            if not self.project.visual_prompts_data: self._generate_visual_prompts()
            if not self.project.visuals_data: self._generate_images()
            self._generate_props()
            return True
        except Exception as e:
            self.project.set_error(str(e))
            return False
