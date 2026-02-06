import logging
from celery import shared_task
from .models import VideoProject
from .services.processor import VideoProcessor

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_video_task(self, project_id):
    """
    Background task to process video segments.
    Phase 1: Analysis (transcribe, segment, map, image gen) -> Result: 'ready'
    Phase 2: User Review (manual)
    Phase 3: Render (MoviePy) -> Result: 'completed'
    """
    try:
        project = VideoProject.objects.get(id=project_id)
        logger.info(f"Processing video project {project_id} [Status: {project.status}]...")
        
        processor = VideoProcessor(project)
        
        if project.status in ['draft', 'analyzing', 'pending']:
            success = processor.run_analysis()
        elif project.status in ['ready', 'rendering']:
            success = processor.run_render()
        else:
            logger.warning(f"Project {project_id} is in status {project.status}, nothing to do.")
            return {"status": "skipped", "reason": "invalid_status"}
        
        if success:
            logger.info(f"Successfully moved project {project_id} to next stage.")
            return {"status": "success", "project_id": project_id, "next_status": project.status}
        else:
            logger.error(f"Failed project {project_id}: {project.error_message}")
            return {"status": "error", "error": project.error_message}
            
    except VideoProject.DoesNotExist:
        logger.error(f"VideoProject {project_id} does not exist.")
        return {"status": "not_found"}
    except Exception as e:
        logger.exception(f"Unexpected error in process_video_task for project {project_id}")
        # Retry logic could be added here
        raise self.retry(exc=e, countdown=60)

@shared_task
def auto_process_pending_projects():
    """
    Periodic task to automatically pick up 'pending' or 'draft' projects for analysis.
    """
    # Pickup projects that are 'pending' (legacy) or 'draft'
    pending_projects = VideoProject.objects.filter(status__in=['pending', 'draft'])
    count = pending_projects.count()
    if count > 0:
        logger.info(f"Auto-picking {count} projects for analysis...")
        for project in pending_projects:
            process_video_task.delay(project.id)
    return f"Processed {count} projects"
