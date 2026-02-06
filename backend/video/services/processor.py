from pathlib import Path
from ..models import VideoProject, VisualAsset, VideoSegment
from .ai import (
    ImageGenerationService,
    TranscriptionService,
    VisualMappingService,
)
from .video_editor import VideoEditorService
from ..utils import get_media_paths

class VideoProcessor:
    def __init__(self, project: VideoProject):
        self.project = project
        self.paths = get_media_paths()

    def run_analysis(self) -> bool:
        """
        Phase 1: Ingestion & Analysis
        Transcribes and creates initial segments.
        Stops at 'ready' for user review.
        """
        try:
            self._transcribe()
            self._create_segments()
            self._generate_visual_prompts()
            self._generate_images()
            self.project.update_status('ready', 'Analysis complete. Ready for review.')
            return True
        except Exception as e:
            self.project.set_error(str(e))
            return False

    def run_render(self) -> bool:
        """
        Phase 3: Rendering Engine
        Processes segments into a final video.
        """
        try:
            self._render_video()
            return True
        except Exception as e:
            self.project.set_error(str(e))
            return False

    def run(self) -> bool:
        # Compatibility method: does the whole thing if called
        if self.run_analysis():
            return self.run_render()
        return False

    def _transcribe(self):
        self.project.update_status('analyzing', 'Transcribing audio...')
        provider = self.project.transcription_provider
        service = TranscriptionService(provider=provider)
        self.project.transcript_data = service.transcribe(self.project.raw_video.path)
        self.project.save()

    def _create_segments(self):
        """
        Task 2: Parse Whisper JSON into segments (1-5s intervals).
        """
        self.project.update_status('analyzing', 'Creating video segments...')
        transcript_data = self.project.transcript_data or []
        
        # Simple segmenting logic: Group whisper segments into 1-5 second chunks
        # or just use whisper's segments if they are small enough.
        # For now, let's just create one VideoSegment per whisper segment to be safe.
        
        # Clear existing segments
        self.project.segments.all().delete()
        
        for i, entry in enumerate(transcript_data):
            VideoSegment.objects.create(
                project=self.project,
                order=i,
                start_time=entry.get('start', 0),
                end_time=entry.get('end', 0),
                transcript=entry.get('text', ''),
                layout_event='split',
                animation_type='ken_burns'
            )

    def _generate_visual_prompts(self):
        self.project.update_status('analyzing', 'Generating visual prompts...')
        provider = self.project.llm_provider
        mapper = VisualMappingService(provider=provider)
        
        # In PRD v2, we map prompts per segment
        segments = self.project.segments.all()
        transcript_for_mapping = [
            {'start': s.start_time, 'end': s.end_time, 'text': s.transcript}
            for s in segments
        ]
        
        prompts = mapper.generate_visual_prompts(
            transcript_for_mapping,
            style_hint=self.project.style_hint
        )
        self.project.visual_prompts_data = prompts
        self.project.save()

    def _generate_images(self):
        if self.project.skip_image_generation:
            return

        self.project.update_status('analyzing', 'Generating AI assets...')
        provider = self.project.image_provider
        generator = ImageGenerationService(provider=provider)

        prompts_data = self.project.visual_prompts_data or []
        visuals = generator.generate_batch(
            prompts_data,
            str(self.paths['assets'])
        )

        segments = self.project.segments.all().order_by('order')
        for i, segment in enumerate(segments):
            if i < len(visuals):
                asset_url = visuals[i].get('src', '')
                # asset_url is like /media/assets/filename
                filename = asset_url.split('/')[-1]
                segment.asset_file = f"assets/{filename}"
                segment.asset_type = 'ai_image'
                segment.save()

        self.project.visuals_data = visuals
        self.project.save()

    def _render_video(self):
        self.project.update_status('rendering', 'Rendering final video...')
        
        output_filename = f"final_{self.project.id}.mp4"
        output_path = str(self.paths['output'] / output_filename)
        
        # Fetch segments with assets
        segments = self.project.segments.all().order_by('order')
        
        editor = VideoEditorService(output_path=output_path)
        editor.edit_video_v2(
            base_video_path=self.project.raw_video.path,
            segments=segments
        )
        
        self.project.output_video = f"output/{output_filename}"
        self.project.update_status('completed', 'Rendered successfully!')
        self.project.save()

    def generate_ai_assets_only(self) -> bool:
        return self.run_analysis()
