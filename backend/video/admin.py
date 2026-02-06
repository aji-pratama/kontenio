"""
Video Admin
-----------
Django Admin interface for the AI Video Factory.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import VideoProject, VisualAsset
from .services import VideoProcessingService


class VisualAssetInline(admin.TabularInline):
    """Inline display of visual assets for a project."""
    model = VisualAsset
    extra = 0
    readonly_fields = ['image_preview', 'created_at']
    fields = ['start_time', 'image', 'image_preview', 'prompt', 'is_generated']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px; border-radius: 8px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    """Admin interface for VideoProject."""
    
    list_display = [
        'title', 
        'status_badge', 
        'video_preview',
        'created_at', 
        'actions_column'
    ]
    list_filter = ['status', 'created_at', 'use_api_transcription']
    search_fields = ['title', 'description']
    readonly_fields = [
        'status', 
        'progress_message', 
        'error_message',
        'transcript_data',
        'visual_prompts_data',
        'visuals_data',
        'output_video',
        'props_file',
        'created_at', 
        'updated_at', 
        'completed_at',
        'video_player',
        'output_player',
    ]
    
    fieldsets = (
        ('Project Info', {
            'fields': ('title', 'description', 'raw_video', 'video_player')
        }),
        ('Processing Options', {
            'fields': ('style_hint', 'use_api_transcription', 'skip_image_generation')
        }),
        ('Status', {
            'fields': ('status', 'progress_message', 'error_message')
        }),
        ('Generated Data', {
            'fields': ('transcript_data', 'visual_prompts_data', 'visuals_data'),
            'classes': ('collapse',)
        }),
        ('Output', {
            'fields': ('output_video', 'output_player', 'props_file')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [VisualAssetInline]
    
    actions = ['process_videos', 'process_videos_mock', 'generate_props_only']
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'pending': '#6c757d',
            'transcribing': '#17a2b8',
            'mapping': '#17a2b8',
            'generating': '#ffc107',
            'rendering': '#fd7e14',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def video_preview(self, obj):
        """Show thumbnail/preview of raw video."""
        if obj.raw_video:
            return format_html(
                '<span style="color: #666; font-size: 12px;">📹 {}</span>',
                obj.raw_video_filename
            )
        return "-"
    video_preview.short_description = 'Input'
    
    def video_player(self, obj):
        """Embed video player for raw video."""
        if obj.raw_video:
            return format_html(
                '<video width="400" controls style="border-radius: 8px; max-width: 100%;">'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support video.'
                '</video>',
                obj.raw_video.url
            )
        return "No video uploaded"
    video_player.short_description = 'Input Video Preview'
    
    def output_player(self, obj):
        """Embed video player for output video."""
        if obj.output_video:
            return format_html(
                '<video width="300" controls style="border-radius: 8px;">'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support video.'
                '</video>',
                obj.output_video.url
            )
        return "Not yet rendered"
    output_player.short_description = 'Output Video Preview'
    
    def actions_column(self, obj):
        """Custom actions column."""
        if obj.status == 'completed' and obj.output_video:
            return format_html(
                '<a href="{}" class="button" style="padding: 4px 8px; '
                'background: #28a745; color: white; text-decoration: none; '
                'border-radius: 4px; font-size: 11px;">⬇ Download</a>',
                obj.output_video.url
            )
        elif obj.status == 'pending':
            return format_html(
                '<span style="color: #666; font-size: 11px;">Ready to process</span>'
            )
        elif obj.status == 'failed':
            return format_html(
                '<span style="color: #dc3545; font-size: 11px;">❌ Failed</span>'
            )
        else:
            return format_html(
                '<span style="color: #17a2b8; font-size: 11px;">⏳ Processing...</span>'
            )
    actions_column.short_description = 'Actions'
    
    # Admin Actions
    @admin.action(description='🚀 Process selected videos (Production)')
    def process_videos(self, request, queryset):
        """Process selected videos with real AI services."""
        for project in queryset.filter(status=VideoProject.Status.PENDING):
            service = VideoProcessingService(project, use_mock=False)
            success = service.process()
            if success:
                messages.success(request, f'✅ {project.title} processed successfully!')
            else:
                messages.error(request, f'❌ {project.title} failed: {project.error_message}')
    
    @admin.action(description='🧪 Process selected videos (Mock/Test)')
    def process_videos_mock(self, request, queryset):
        """Process selected videos with mock data (no API calls)."""
        for project in queryset.filter(status=VideoProject.Status.PENDING):
            service = VideoProcessingService(project, use_mock=True)
            success = service.process()
            if success:
                messages.success(request, f'✅ {project.title} processed successfully (mock mode)!')
            else:
                messages.error(request, f'❌ {project.title} failed: {project.error_message}')
    
    @admin.action(description='📝 Generate props only (no render)')
    def generate_props_only(self, request, queryset):
        """Generate props file without rendering."""
        for project in queryset:
            service = VideoProcessingService(project, use_mock=True)
            success = service.generate_props_only()
            if success:
                messages.success(request, f'✅ Props generated for {project.title}')
            else:
                messages.error(request, f'❌ Failed to generate props for {project.title}')


@admin.register(VisualAsset)
class VisualAssetAdmin(admin.ModelAdmin):
    """Admin interface for VisualAsset."""
    
    list_display = ['project', 'start_time', 'image_preview', 'is_generated', 'created_at']
    list_filter = ['is_generated', 'project']
    search_fields = ['project__title', 'prompt']
    readonly_fields = ['image_preview_large', 'created_at']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px; max-width: 100px; border-radius: 4px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 400px; border-radius: 8px;" />',
                obj.image.url
            )
        return "-"
    image_preview_large.short_description = "Image Preview"
