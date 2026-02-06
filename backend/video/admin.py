from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import VideoProject, VisualAsset, VideoSegment, VideoTemplate
from .services.processor import VideoProcessor

@admin.register(VideoTemplate)
class VideoTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']

class VideoSegmentInline(admin.TabularInline):
    model = VideoSegment
    extra = 0
    fields = ['order', 'start_time', 'end_time', 'transcript', 'layout_event', 'asset_file']

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
    list_display = ['title', 'status_badge', 'template', 'created_at', 'actions_column']
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = [
        'status', 'progress_message', 'error_message',
        'transcript_data', 'visual_prompts_data', 'visuals_data',
        'output_video', 'props_file',
        'created_at', 'updated_at', 'completed_at',
        'video_player', 'output_player',
    ]
    fieldsets = (
        ('Project Info', {'fields': ('title', 'template', 'description', 'raw_video', 'video_player')}),
        ('AI Providers', {'fields': ('transcription_provider', 'llm_provider', 'image_provider')}),
        ('Options', {'fields': ('style_hint', 'skip_image_generation', 'global_style')}),
        ('Status', {'fields': ('status', 'progress_message', 'error_message')}),
        ('Data', {'fields': ('transcript_data', 'visual_prompts_data', 'visuals_data'), 'classes': ('collapse',)}),
        ('Output', {'fields': ('output_video', 'output_player', 'props_file')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'completed_at'), 'classes': ('collapse',)}),
    )
    inlines = [VideoSegmentInline, VisualAssetInline]
    actions = ['process_videos', 'process_videos_mock', 'retry_projects', 'force_render']

    class Media:
        js = ('admin/js/project_refresh.js',)

    def changelist_view(self, request, extra_context=None):
        # Auto-refresh if any project is in a processing state
        processing_exists = VideoProject.objects.filter(
            status__in=['transcribing', 'mapping', 'generating', 'rendering']
        ).exists()
        extra_context = extra_context or {}
        extra_context['processing_active'] = processing_exists
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='🔄 Retry Selected (Set to Pending)')
    def retry_projects(self, request, queryset):
        count = queryset.update(status='pending', error_message='', progress_message='Retrying...')
        messages.success(request, f'✅ {count} projects reset to Pending. Celery Beat will pick them up shortly.')

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

    @admin.action(description='🚀 Process (Auto-detect Phase)')
    def process_videos(self, request, queryset):
        from .tasks import process_video_task
        count = 0
        for project in queryset.filter(status__in=['draft', 'ready', 'failed', 'pending']):
            project.error_message = "" # Clear errors on retry
            project.save()
            process_video_task.delay(project.id)
            count += 1
        messages.success(request, f'✅ {count} projects queued for processing.')

    @admin.action(description='🧪 Process Mock (Force Phase 1)')
    def process_videos_mock(self, request, queryset):
        from .tasks import process_video_task
        count = 0
        for project in queryset.filter(status__in=['draft', 'failed', 'pending']):
            # Force mock providers and SAVE to DB
            project.transcription_provider = 'mock'
            project.llm_provider = 'mock'
            project.image_provider = 'mock'
            project.error_message = ""
            project.save() 
            
            process_video_task.delay(project.id)
            count += 1
        messages.success(request, f'✅ {count} projects submitted for Mock Analysis.')

    @admin.action(description='⏩ Force Render (Ready -> Complete)')
    def force_render(self, request, queryset):
        from .tasks import process_video_task
        count = 0
        for project in queryset.filter(status='ready'):
             process_video_task.delay(project.id)
             count += 1
        messages.success(request, f'✅ {count} projects queued for rendering.')


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
