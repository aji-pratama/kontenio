"""
Video Models
------------
Database models for the AI Video Factory.
"""

import os
import json
from pathlib import Path
from django.db import models
from django.conf import settings
from django.utils import timezone


class VideoProject(models.Model):
    """
    Represents a video project/rendering job.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        TRANSCRIBING = 'transcribing', 'Transcribing'
        MAPPING = 'mapping', 'Mapping Visuals'
        GENERATING = 'generating', 'Generating Images'
        RENDERING = 'rendering', 'Rendering Video'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    # Basic info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Input video
    raw_video = models.FileField(upload_to='raw/')
    
    # Processing options
    style_hint = models.CharField(
        max_length=255, 
        default='modern, cinematic, vibrant',
        help_text='Style hint for AI visual generation'
    )
    use_api_transcription = models.BooleanField(
        default=True,
        help_text='Use OpenAI API for transcription (vs local Whisper)'
    )
    skip_image_generation = models.BooleanField(
        default=False,
        help_text='Skip AI image generation (use placeholder visuals)'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress_message = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Generated data (stored as JSON)
    transcript_data = models.JSONField(null=True, blank=True)
    visual_prompts_data = models.JSONField(null=True, blank=True)
    visuals_data = models.JSONField(null=True, blank=True)
    
    # Output
    output_video = models.FileField(upload_to='output/', null=True, blank=True)
    props_file = models.FileField(upload_to='props/', null=True, blank=True)
    
    # Timestamps
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
        """Get just the filename from the raw_video path."""
        if self.raw_video:
            return os.path.basename(self.raw_video.name)
        return None
    
    @property
    def output_video_url(self):
        """Get URL to output video if it exists."""
        if self.output_video:
            return self.output_video.url
        return None
    
    def update_status(self, status, message=''):
        """Update the project status and save."""
        self.status = status
        self.progress_message = message
        if status == self.Status.COMPLETED:
            self.completed_at = timezone.now()
        self.save(update_fields=['status', 'progress_message', 'completed_at', 'updated_at'])
    
    def set_error(self, error_message):
        """Mark the project as failed with an error message."""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])


class VisualAsset(models.Model):
    """
    Represents a generated or uploaded visual asset for a project.
    """
    
    project = models.ForeignKey(
        VideoProject, 
        on_delete=models.CASCADE, 
        related_name='visual_assets'
    )
    
    # Timing
    start_time = models.FloatField(help_text='Start time in seconds')
    
    # Image
    image = models.ImageField(upload_to='assets/')
    
    # Generation info
    prompt = models.TextField(blank=True, help_text='AI prompt used to generate this image')
    is_generated = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        verbose_name = 'Visual Asset'
        verbose_name_plural = 'Visual Assets'
    
    def __str__(self):
        return f"Visual at {self.start_time}s for {self.project.title}"
    
    @property
    def src_path(self):
        """Get the relative path for Remotion props."""
        if self.image:
            return f"/media/{self.image.name}"
        return None
