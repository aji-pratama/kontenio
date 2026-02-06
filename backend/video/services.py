import subprocess
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
        self.project.save(update_fields=['transcript_data', 'updated_at'])

    def _generate_visual_prompts(self):
        provider = self.project.llm_provider
        provider_display = self.project.get_llm_provider_display()
        self.project.update_status('mapping', f'Mapping with {provider_display}...')

        mapper = VisualMappingService(provider=provider)
        self.project.visual_prompts_data = mapper.generate_visual_prompts(
            self.project.transcript_data,
            style_hint=self.project.style_hint
        )
        self.project.save(update_fields=['visual_prompts_data', 'updated_at'])

    def _generate_images(self):
        if self.project.skip_image_generation:
            self.project.visuals_data = []
            self.project.save(update_fields=['visuals_data'])
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
        for i, prompt_obj in enumerate(self.project.visual_prompts_data or []):
            if i < len(visuals):
                filename = visuals[i]['src'].split('/')[-1]
                VisualAsset.objects.create(
                    project=self.project,
                    start_time=prompt_obj['time'],
                    image=f"assets/{filename}",
                    prompt=prompt_obj.get('prompt', ''),
                    is_generated=(provider != 'mock')
                )

        self.project.visuals_data = visuals
        self.project.save(update_fields=['visuals_data', 'updated_at'])

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
        self.project.save(update_fields=['props_file', 'updated_at'])

    def _render(self):
        self.project.update_status('rendering', 'Rendering video...')

        try:
            metadata = get_video_metadata(self.project.raw_video.path)
            duration_frames = int(metadata['duration'] * 30)
        except Exception:
            duration_frames = 300

        output_filename = f"final_{self.project.id}.mp4"
        output_path = self.paths['output'] / output_filename
        props_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'

        cmd = [
            "npx", "remotion", "render", "SplitScreen",
            str(output_path), f"--props={props_path}", f"--frames=0-{duration_frames}"
        ]

        subprocess.run(cmd, cwd=str(settings.PROJECT_ROOT), capture_output=True, text=True, check=True, timeout=600)
        
        self.project.output_video = f"output/{output_filename}"
        self.project.update_status('completed', 'Done!')
        self.project.save(update_fields=['output_video', 'updated_at'])

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
