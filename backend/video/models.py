import os
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


class VideoProject(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('transcribing', 'Transcribing'),
        ('mapping', 'Mapping Visuals'),
        ('generating', 'Generating Images'),
        ('rendering', 'Rendering Video'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    TRANSCRIPTION_CHOICES = (
        ('openai_whisper', 'OpenAI Whisper'),
        ('gemini', 'Gemini Audio'),
        ('local_whisper', 'Local Whisper'),
        ('mock', 'Mock (Testing)'),
    )

    LLM_CHOICES = (
        ('openai_gpt4', 'GPT-4o'),
        ('openai_gpt4_mini', 'GPT-4o Mini'),
        ('gemini_pro', 'Gemini Pro'),
        ('gemini_flash', 'Gemini Flash'),
        ('mock', 'Mock (Testing)'),
    )

    IMAGE_CHOICES = (
        ('dalle3', 'DALL-E 3'),
        ('imagen', 'Imagen 3'),
        ('gemini_flash', 'Gemini Flash'),
        ('mock', 'Mock (Testing)'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    raw_video = models.FileField(upload_to='raw/')

    style_hint = models.CharField(
        max_length=255,
        default=getattr(settings, 'DEFAULT_STYLE_HINT', 'modern')
    )
    transcription_provider = models.CharField(
        max_length=20,
        choices=TRANSCRIPTION_CHOICES,
        default=getattr(settings, 'DEFAULT_TRANSCRIPTION_PROVIDER', 'openai_whisper')
    )
    llm_provider = models.CharField(
        max_length=20,
        choices=LLM_CHOICES,
        default=getattr(settings, 'DEFAULT_LLM_PROVIDER', 'openai_gpt4')
    )
    image_provider = models.CharField(
        max_length=20,
        choices=IMAGE_CHOICES,
        default=getattr(settings, 'DEFAULT_IMAGE_PROVIDER', 'dalle3')
    )
    skip_image_generation = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    progress_message = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    transcript_data = models.JSONField(null=True, blank=True)
    visual_prompts_data = models.JSONField(null=True, blank=True)
    visuals_data = models.JSONField(null=True, blank=True)

    output_video = models.FileField(upload_to='output/', null=True, blank=True)
    props_file = models.FileField(upload_to='props/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Video Project'
        verbose_name_plural = 'Video Projects'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def raw_video_filename(self):
        if self.raw_video:
            return os.path.basename(self.raw_video.name)
        return None

    @property
    def output_video_url(self):
        if self.output_video:
            return self.output_video.url
        return None

    def update_status(self, status, message=''):
        self.status = status
        self.progress_message = message
        if status == 'completed':
            self.completed_at = timezone.now()
        self.save()

    def set_error(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save()


class VisualAsset(models.Model):
    project = models.ForeignKey(
        VideoProject,
        on_delete=models.CASCADE,
        related_name='visual_assets'
    )
    start_time = models.FloatField()
    image = models.ImageField(upload_to='assets/')
    prompt = models.TextField(blank=True)
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Visual Asset'
        verbose_name_plural = 'Visual Assets'

    def __str__(self):
        return f"Visual at {self.start_time}s for {self.project.title}"

    @property
    def src_path(self):
        if self.image:
            return f"/media/{self.image.name}"
        return None
