import json
import os
from pathlib import Path
from unittest import mock
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import VideoProject, VisualAsset
from .services import VideoProcessingService
from .providers import ProviderFactory

class VideoFactoryTests(TestCase):
    def setUp(self):
        # Create a dummy video file
        self.video_content = b'fake video content'
        self.video_file = SimpleUploadedFile(
            "test_video.mp4", 
            self.video_content, 
            content_type="video/mp4"
        )
        
        # Create a project with mock providers
        self.project = VideoProject.objects.create(
            title="Test Project",
            raw_video=self.video_file,
            transcription_provider='mock',
            llm_provider='mock',
            image_provider='mock',
            style_hint='cyberpunk'
        )

    def test_provider_factory(self):
        """Test if the factory returns the correct mock providers"""
        factory = ProviderFactory()
        self.assertEqual(factory.get_transcription_provider('mock').name, "Mock Transcriber")
        self.assertEqual(factory.get_llm_provider('mock').name, "Mock LLM")
        self.assertEqual(factory.get_image_provider('mock').name, "Mock Image Gen")

    def test_props_generation_paths(self):
        """
        CRITICAL: Test that generated props use file:// paths for stability
        """
        service = VideoProcessingService(self.project)
        
        # Populate dummy data needed for props
        self.project.transcript_data = [{'start': 0, 'end': 1, 'text': 'test'}]
        self.project.visuals_data = [{'start': 0, 'src': '/media/assets/test.jpg'}]
        self.project.save()
        
        # We need to mock ensure_symlink to basically do nothing in test env
        with mock.patch('video.services.ensure_symlink'):
            service._generate_props()
            
        # Verify the file was created in the media root
        props_path = Path(settings.MEDIA_ROOT) / 'props' / f'props_project_{self.project.id}.json'
        self.assertTrue(props_path.exists(), "Props file was not created")
        
        with open(props_path, 'r') as f:
            data = json.load(f)
            
        # VERIFY 1: Video URL
        video_url = data.get('videoUrl', '')
        self.assertTrue(video_url.startswith('http'), f"Video URL must be http, got: {video_url}")
        self.assertIn(':8001', video_url, "Video URL must use port 8001")
        
        # VERIFY 2: Visuals URL
        visual_url = data['visuals'][0]['src']
        self.assertTrue(visual_url.startswith('http'), f"Visual URL must be http, got: {visual_url}")
        self.assertIn(':8001', visual_url, "Visual URL must use port 8001")

    def test_render_command_arguments(self):
        """
        Test that the Remotion render command includes correct concurrency settings.
        Security flags are removed in favor of HTTP strategy.
        """
        service = VideoProcessingService(self.project)
        
        # Populate data
        service._transcribe()
        service._generate_visual_prompts()
        service._generate_images()
        service._generate_props()
        
        # Mock subprocess.run
        with mock.patch('subprocess.run') as mock_run:
            with mock.patch('video.services.get_video_metadata') as mock_meta:
                mock_meta.return_value = {'duration': 10.0}
                
                service._render()
                
                # Check args
                self.assertTrue(mock_run.called)
                args = mock_run.call_args[0][0] # The cmd list
                joined_args = " ".join(args)
                
                # Check performance/stability limits
                self.assertIn("--concurrency=1", joined_args)
                self.assertIn("--timeout=120000", joined_args)

    def test_full_pipeline_mock_execution(self):
        """Test the entire pipeline runs without error using mocks (Logic only)"""
        service = VideoProcessingService(self.project)
        
        with mock.patch('subprocess.run') as mock_run:
            with mock.patch('video.services.get_video_metadata') as mock_meta:
                mock_meta.return_value = {'duration': 10.0}
                
                success = service.process()
                
                self.assertTrue(success)
                self.project.refresh_from_db()
                self.assertEqual(self.project.status, 'completed')
                self.assertEqual(self.project.error_message, '')

    def tearDown(self):
        # Clean up generated files if they exist
        if hasattr(self, 'project') and self.project.id:
            props_path = Path(settings.MEDIA_ROOT) / 'props' / f'props_project_{self.project.id}.json'
            if props_path.exists():
                os.remove(props_path)
