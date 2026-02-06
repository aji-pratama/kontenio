import logging
from celery import shared_task
from .models import VideoProject
from .services import VideoProcessingService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_video_task(self, project_id):
    """
    Background task to process video: transcribe, map, generate images, and render.
    """
    try:
        project = VideoProject.objects.get(id=project_id)
        logger.info(f"Processing video project {project_id}...")
        
        service = VideoProcessingService(project)
        success = service.process()
        
        if success:
            logger.info(f"Successfully processed video project {project_id}")
            return {"status": "success", "project_id": project_id}
        else:
            logger.error(f"Failed to process video project {project_id}: {project.error_message}")
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
    Periodic task to automatically pick up 'pending' projects.
    """
    pending_projects = VideoProject.objects.filter(status='pending')
    count = pending_projects.count()
    if count > 0:
        logger.info(f"Auto-picking {count} pending projects...")
        for project in pending_projects:
            # We use delay() to process each one in its own worker thread
            process_video_task.delay(project.id)
    return f"Processed {count} projects"
