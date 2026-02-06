from typing import List
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from .models import VideoProject, VideoSegment
from .services.processor import VideoProcessor

api = NinjaAPI(title="Kontenio API", version="1.0.0")

# --- Schemas ---

class ErrorSchema(Schema):
    message: str

class SegmentSchema(Schema):
    id: int
    order: int
    start_time: float
    end_time: float
    transcript: str
    asset_type: str
    asset_file: str = None
    layout_event: str
    animation_type: str

    @staticmethod
    def resolve_asset_file(obj):
        return obj.asset_file.url if obj.asset_file else None

class ProjectSchema(Schema):
    id: int
    title: str
    status: str
    status_display: str
    progress_message: str
    error_message: str
    raw_video_url: str = None
    output_video_url: str = None
    created_at: str

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()
    
    @staticmethod
    def resolve_raw_video_url(obj):
        return obj.raw_video.url if obj.raw_video else None
    
    @staticmethod
    def resolve_output_video_url(obj):
        return obj.output_video.url if obj.output_video else None

# --- Endpoints ---

@api.get("/projects", response=List[ProjectSchema])
def list_projects(request):
    return VideoProject.objects.all()

@api.get("/projects/{project_id}", response=ProjectSchema)
def get_project(request, project_id: int):
    return get_object_or_404(VideoProject, id=project_id)

@api.post("/projects", response={201: ProjectSchema})
def create_project(request, title: str, video_file: UploadedFile = File(...)):
    project = VideoProject.objects.create(
        title=title,
        raw_video=video_file,
        status='draft'
    )
    return 201, project

@api.post("/projects/{project_id}/analyze")
def analyze_project(request, project_id: int):
    """
    Triggers Phase 1: Ingestion & Analysis (Async)
    """
    from .tasks import process_video_task
    project = get_object_or_404(VideoProject, id=project_id)
    project.update_status('analyzing', 'Starting analysis...')
    process_video_task.delay(project_id)
    return {"status": "success", "message": "Analysis started in background"}

@api.get("/projects/{project_id}/segments", response=List[SegmentSchema])
def list_segments(request, project_id: int):
    project = get_object_or_404(VideoProject, id=project_id)
    return project.segments.all()

@api.patch("/segments/{segment_id}")
def update_segment(request, segment_id: int, data: dict):
    segment = get_object_or_404(VideoSegment, id=segment_id)
    for attr, value in data.items():
        setattr(segment, attr, value)
    segment.save()
    return {"status": "success"}

@api.post("/projects/{project_id}/render")
def render_project(request, project_id: int):
    """
    Triggers Phase 3: Rendering (Async)
    """
    from .tasks import process_video_task # Using same task for compatibility
    project = get_object_or_404(VideoProject, id=project_id)
    project.update_status('rendering', 'Setting up render...')
    # Normally we'd have a separate render task or a flag
    process_video_task.delay(project_id) 
    return {"status": "success", "message": "Rendering started"}
