from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from video.models import VideoProject
from video.services.processor import VideoProcessor
from video.utils import get_media_paths

class Command(BaseCommand):
    help = 'Orchestrate the AI Video Factory pipeline'

    def add_arguments(self, parser):
        parser.add_argument('--input', type=str, required=True, help='Filename in media/raw/')
        parser.add_argument('--project-id', type=int, help='Existing Project ID (optional)')
        parser.add_argument('--mock', action='store_true', help='Use mock providers for testing')
        parser.add_argument('--style', type=str, default='modern, cinematic', help='Style hint')
        parser.add_argument('--async-task', action='store_true', help='Process in background via Celery')
        parser.add_argument('--phase', type=str, choices=['all', 'analysis', 'render'], default='all', help='Pipeline phase')

    def handle(self, *args, **options):
        filename = options['input']
        use_mock = options['mock']
        project_id = options.get('project_id')
        
        paths = get_media_paths()
        raw_path = paths['raw'] / filename
        
        self.stdout.write(self.style.WARNING(f"🚀 AI Video Factory: {filename}"))

        if project_id:
            try:
                project = VideoProject.objects.get(id=project_id)
                self.stdout.write(f"   Using existing project ID: {project.id}")
            except VideoProject.DoesNotExist:
                raise CommandError(f"Project ID {project_id} not found")
        else:
            if not raw_path.exists():
                raise CommandError(f"File not found: {raw_path}")

            project = VideoProject(
                title=f"CLI: {filename}",
                raw_video=f"raw/{filename}",
                style_hint=options['style']
            )
            
            if use_mock:
                project.transcription_provider = 'mock'
                project.llm_provider = 'mock'
                project.image_provider = 'mock'
            
            project.save()
            self.stdout.write(f"   Created new project ID: {project.id}")

        self.stdout.write(f"   Mode: {'Mock' if use_mock else 'Production'}")
        
        if options['async_task']:
            from video.tasks import process_video_task
            process_video_task.delay(project.id)
            self.stdout.write(self.style.SUCCESS(f"\n✅ Task submitted to Celery! Project ID: {project.id}"))
            return

        # Synchronous Execution
        processor = VideoProcessor(project)
        success = False
        
        phase = options['phase']
        
        if phase == 'analysis':
            success = processor.run_analysis()
        elif phase == 'render':
            success = processor.run_render()
        else: # all
            self.stdout.write("   Running Phase 1: Analysis...")
            if processor.run_analysis():
                self.stdout.write("   Running Phase 3: Rendering...")
                success = processor.run_render()
            else:
                success = False

        if success:
            self.stdout.write(self.style.SUCCESS(f"\n🎉 Success! Check media/output/ for results."))
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed: {project.error_message}"))
            raise CommandError(project.error_message)
