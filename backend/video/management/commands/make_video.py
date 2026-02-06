from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from video.models import VideoProject
from video.services import VideoProcessingService
from video.utils import get_media_paths, validate_video_file


class Command(BaseCommand):
    help = 'Orchestrate the AI Video Factory pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--input', type=str, required=True, help='Filename in media/raw/')
        parser.add_argument('--mock', action='store_true', help='Use mock providers for testing')
        parser.add_argument('--style', type=str, default='modern, cinematic', help='Style hint')
        parser.add_argument('--skip-render', action='store_true', help='Generate props only')

    def handle(self, *args, **options):
        filename = options['input']
        use_mock = options['mock']
        
        paths = get_media_paths()
        raw_path = paths['raw'] / filename
        
        self.stdout.write(self.style.WARNING(f"🚀 AI Video Factory: {filename}"))

        if not raw_path.exists():
            raise CommandError(f"File not found: {raw_path}")

        # Create a temporary/adhoc project for this command
        project = VideoProject(
            title=f"CLI: {filename}",
            raw_video=f"raw/{filename}",
            style_hint=options['style']
        )
        
        if use_mock:
            project.transcription_provider = 'mock'
            project.llm_provider = 'mock'
            project.image_provider = 'mock'

        self.stdout.write(f"   Mode: {'Mock' if use_mock else 'Production'}")
        
        service = VideoProcessingService(project)
        
        if options['skip_render']:
            success = service.generate_props_only()
        else:
            success = service.process()

        if success:
            self.stdout.write(self.style.SUCCESS(f"\n🎉 Success! Check media/output/ for results."))
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed: {project.error_message}"))
            raise CommandError(project.error_message)
