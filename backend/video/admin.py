from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import VideoProject, VisualAsset
from .services import VideoProcessingService


class VisualAssetInline(admin.TabularInline):
    model = VisualAsset
    extra = 0
    readonly_fields = ['image_preview', 'created_at']
    fields = ['start_time', 'image', 'image_preview', 'prompt', 'is_generated']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; border-radius: 8px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(VideoProject)
class VideoProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'status_badge', 'providers_display', 'video_preview', 'created_at', 'actions_column']
    list_filter = ['status', 'created_at', 'transcription_provider', 'llm_provider', 'image_provider']
    search_fields = ['title', 'description']
    readonly_fields = [
        'progress_message', 'error_message',
        'transcript_data', 'visual_prompts_data', 'visuals_data',
        'output_video', 'props_file',
        'created_at', 'updated_at', 'completed_at',
        'video_player', 'output_player',
    ]
    fieldsets = (
        ('Project Info', {'fields': ('title', 'description', 'raw_video', 'video_player')}),
        ('AI Providers', {'fields': ('transcription_provider', 'llm_provider', 'image_provider')}),
        ('Options', {'fields': ('style_hint', 'skip_image_generation')}),
        ('Status', {'fields': ('status', 'progress_message', 'error_message')}),
        ('Data', {'fields': ('transcript_data', 'visual_prompts_data', 'visuals_data'), 'classes': ('collapse',)}),
        ('Output', {'fields': ('output_video', 'output_player', 'props_file')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'completed_at'), 'classes': ('collapse',)}),
    )
    inlines = [VisualAssetInline]
    actions = ['process_videos', 'process_videos_mock', 'generate_props_only']

    def providers_display(self, obj):
        return format_html(
            '<span style="font-size: 10px; color: #666;">🎤{} | 🧠{} | 🖼️{}</span>',
            obj.get_transcription_provider_display()[:8],
            obj.get_llm_provider_display()[:8],
            obj.get_image_provider_display()[:8]
        )
    providers_display.short_description = 'Providers'

    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d', 'transcribing': '#17a2b8', 'mapping': '#17a2b8',
            'generating': '#ffc107', 'rendering': '#fd7e14',
            'completed': '#28a745', 'failed': '#dc3545',
        }
        return format_html(
            '<span style="background:{}; color:#fff; padding:4px 12px; '
            'border-radius:12px; font-size:11px;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def video_preview(self, obj):
        if obj.raw_video:
            return format_html('<span style="color:#666; font-size:12px;">📹 {}</span>', obj.raw_video_filename)
        return "-"
    video_preview.short_description = 'Input'

    def video_player(self, obj):
        if obj.raw_video:
            return format_html(
                '<video width="400" controls style="border-radius:8px;">'
                '<source src="{}" type="video/mp4"></video>',
                obj.raw_video.url
            )
        return "No video"
    video_player.short_description = 'Preview'

    def output_player(self, obj):
        if obj.output_video:
            return format_html(
                '<video width="300" controls style="border-radius:8px;">'
                '<source src="{}" type="video/mp4"></video>',
                obj.output_video.url
            )
        return "Not rendered"
    output_player.short_description = 'Output'

    def actions_column(self, obj):
        if obj.status == 'completed' and obj.output_video:
            return format_html(
                '<a href="{}" style="padding:4px 8px; background:#28a745; color:#fff; '
                'text-decoration:none; border-radius:4px; font-size:11px;">⬇ Download</a>',
                obj.output_video.url
            )
        if obj.status == 'failed':
            error_preview = (obj.error_message[:50] + '...') if obj.error_message else 'Unknown error'
            return format_html(
                '<span style="color:#dc3545; font-size:11px;" title="{}"">❌ {}</span>',
                obj.error_message or 'Unknown error',
                error_preview
            )
        if obj.status == 'completed' and obj.error_message:
            # Completed but with errors (partial success)
            return format_html(
                '<span style="color:#ffc107; font-size:11px;" title="{}">⚠️ Partial</span>',
                obj.error_message[:200]
            )
        if obj.status == 'pending':
            return mark_safe('<span style="color:#666; font-size:11px;">Ready</span>')
        return mark_safe('<span style="color:#17a2b8; font-size:11px;">⏳ Processing</span>')
    actions_column.short_description = 'Actions'

    @admin.action(description='🚀 Process (Production)')
    def process_videos(self, request, queryset):
        for project in queryset.filter(status__in=['pending', 'failed']):
            service = VideoProcessingService(project)
            if service.process():
                messages.success(request, f'✅ {project.title} done!')
            else:
                messages.error(request, f'❌ {project.title}: {project.error_message}')

    @admin.action(description='🧪 Process (Mock)')
    def process_videos_mock(self, request, queryset):
        for project in queryset.filter(status__in=['pending', 'failed']):
            # Force mock providers and SAVE to DB
            project.transcription_provider = 'mock'
            project.llm_provider = 'mock'
            project.image_provider = 'mock'
            project.save() 
            
            service = VideoProcessingService(project)
            if service.process():
                messages.success(request, f'✅ {project.title} done (mock)!')
            else:
                messages.error(request, f'❌ {project.title}: {project.error_message}')

    @admin.action(description='📝 Props only')
    def generate_props_only(self, request, queryset):
        for project in queryset:
            service = VideoProcessingService(project)
            if service.generate_props_only():
                messages.success(request, f'✅ Props for {project.title}')
            else:
                messages.error(request, f'❌ {project.title}: {project.error_message}')


@admin.register(VisualAsset)
class VisualAssetAdmin(admin.ModelAdmin):
    list_display = ['project', 'start_time', 'image_preview', 'is_generated', 'created_at']
    list_filter = ['is_generated', 'project']
    search_fields = ['project__title', 'prompt']
    readonly_fields = ['image_preview_large', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px; border-radius:4px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:300px; border-radius:8px;" />',
                obj.image.url
            )
        return "-"
    image_preview_large.short_description = "Image"
