import os
import json
from pathlib import Path
from unittest import mock
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import VideoProject, VisualAsset
from .services.processor import VideoProcessor
from .services.video_editor import VideoEditorService
from .services.ai import TranscriptionService, VisualMappingService, ImageGenerationService
from .providers import ProviderFactory

class VideoEngineTests(TestCase):
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
            title="Test MoviePy Project",
            raw_video=self.video_file,
            transcription_provider='mock',
            llm_provider='mock',
            image_provider='mock',
            style_hint='modern'
        )

    def test_provider_factory(self):
        """Test if the factory returns the correct mock providers"""
        factory = ProviderFactory()
        self.assertEqual(factory.get_transcription_provider('mock').name, "Mock Transcriber")
        self.assertEqual(factory.get_llm_provider('mock').name, "Mock LLM")
        self.assertEqual(factory.get_image_provider('mock').name, "Mock Image Gen")

    @mock.patch('video.services.video_editor.VideoFileClip')
    @mock.patch('video.services.video_editor.CompositeVideoClip')
    def test_video_editor_logic(self, mock_composite, mock_video_clip):
        """
        Test VideoEditorService initializes and calls MoviePy correctly.
        """
        mock_instance = mock_video_clip.return_value
        mock_instance.duration = 10.0
        mock_instance.subclip.return_value = mock_instance
        mock_instance.resize.return_value = mock_instance
        mock_instance.set_position.return_value = mock_instance
        mock_instance.set_start.return_value = mock_instance
        
        output_path = str(Path(settings.MEDIA_ROOT) / 'output' / 'test_output.mp4')
        editor = VideoEditorService(output_path=output_path)
        
        assets = [{'src': '/media/assets/test.jpg'}]
        transcript = [{'start': 0, 'end': 2, 'text': 'Hello world'}]
        
        # We mock write_videofile to avoid actual rendering
        with mock.patch.object(CompositeVideoClip, 'write_videofile') as mock_write:
            editor.edit_video(
                base_video_path=self.project.raw_video.path,
                assets_data=assets,
                transcript_data=transcript
            )
            self.assertTrue(mock_write.called)

    def test_ai_services_batch_processing(self):
        """
        Test AI services coordination (Transcription, Mapping, Image Gen).
        """
        # 1. Transcription
        transcriber = TranscriptionService(provider='mock')
        transcript = transcriber.transcribe(self.project.raw_video.path)
        self.assertIsInstance(transcript, list)
        self.assertTrue(len(transcript) > 0)
        
        # 2. Mapping
        mapper = VisualMappingService(provider='mock')
        mapping = mapper.generate_visual_prompts(transcript)
        self.assertEqual(len(mapping), len(transcript))
        
        # 3. Image Generation
        generator = ImageGenerationService(provider='mock')
        results = generator.generate_batch(mapping, str(Path(settings.MEDIA_ROOT) / 'assets'))
        self.assertEqual(len(results), len(mapping))

    @mock.patch('video.services.processor.VideoEditorService')
    def test_full_processor_run(self, mock_editor_class):
        """
        Test the VideoProcessor runs the full pipeline successfully.
        """
        mock_editor = mock_editor_class.return_value
        
        processor = VideoProcessor(self.project)
        success = processor.run()
        
        self.assertTrue(success)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'completed')
        self.assertIsNotNone(self.project.output_video.name)
        
        # Check if assets were created in DB
        self.assertTrue(VisualAsset.objects.filter(project=self.project).exists())

    def test_error_handling(self):
        """Test that errors are correctly captured in the project model."""
        with mock.patch('video.services.ai.TranscriptionService.transcribe', side_effect=Exception("API Down")):
            processor = VideoProcessor(self.project)
            success = processor.run()
            
            self.assertFalse(success)
            self.project.refresh_from_db()
            self.assertEqual(self.project.status, 'failed')
            self.assertEqual(self.project.error_message, "API Down")

    def tearDown(self):
        # Clean up any files created during tests
        if self.project.raw_video:
            if os.path.exists(self.project.raw_video.path):
                os.remove(self.project.raw_video.path)
