"""
Configuración de Celery para procesamiento asincrónico de video
"""

from celery import Celery
from config import settings
import logging

logger = logging.getLogger(__name__)

# Crear instancia de Celery
celery_app = Celery(
    "clips_virales",
    broker=settings.celery_broker_url,
    backend=settings.redis_url
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora
    task_soft_time_limit=3300,  # 55 minutos
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # Los resultados expiran en 1 hora
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Configuration for routing
    task_routes={
        "tasks.render_video_task": {"queue": "videos"},
        "tasks.generate_script_task": {"queue": "scripts"},
        "tasks.generate_audio_task": {"queue": "audio"},
        "tasks.collect_broll_task": {"queue": "media"},
    },
)


# Tareas Celery
@celery_app.task(bind=True, name="tasks.generate_script_task")
def generate_script_task(self, video_project_id: int, topic: str, platform: str):
    """
    Tarea asincrónica para generar guión
    """
    try:
        self.update_state(state="PROGRESS", meta={"step": "generating_script", "progress": 0})
        
        from modules_script_generator import get_script_generator
        
        logger.info(f"Generando guión para proyecto {video_project_id}")
        
        generator = get_script_generator(provider="gemini")
        
        # Generar guión (necesita ser síncrono, envolver si es async)
        import asyncio
        script = asyncio.run(generator.generate_script(
            topic=topic,
            platform=platform
        ))
        
        self.update_state(state="PROGRESS", meta={"step": "script_generated", "progress": 100})
        
        return {
            "status": "completed",
            "video_project_id": video_project_id,
            "script": script
        }
    
    except Exception as e:
        logger.error(f"Error en generate_script_task: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="tasks.generate_audio_task")
def generate_audio_task(self, video_project_id: int, text: str, language: str = "es-ES"):
    """
    Tarea asincrónica para sintetizar audio
    """
    try:
        self.update_state(state="PROGRESS", meta={"step": "generating_audio", "progress": 0})
        
        from modules_tts import get_tts_engine
        import asyncio
        
        logger.info(f"Generando audio para proyecto {video_project_id}")
        
        engine = get_tts_engine(provider="elevenlabs")
        audio_path = f"/tmp/clips_virales/audio_{video_project_id}.mp3"
        
        success = asyncio.run(engine.synthesize(
            text=text,
            language=language,
            output_path=audio_path
        ))
        
        self.update_state(state="PROGRESS", meta={"step": "audio_generated", "progress": 100})
        
        return {
            "status": "completed" if success else "failed",
            "video_project_id": video_project_id,
            "audio_path": audio_path if success else None
        }
    
    except Exception as e:
        logger.error(f"Error en generate_audio_task: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="tasks.collect_broll_task")
def collect_broll_task(self, video_project_id: int, keywords: list, quantity: int = 5):
    """
    Tarea asincrónica para recolectar B-Roll
    """
    try:
        self.update_state(state="PROGRESS", meta={"step": "collecting_broll", "progress": 0})
        
        from modules_broll import get_broll_manager
        import asyncio
        
        logger.info(f"Recolectando B-Roll para proyecto {video_project_id}")
        
        manager = get_broll_manager()
        broll = asyncio.run(manager.search_broll(
            keywords=keywords,
            quantity=quantity
        ))
        
        self.update_state(state="PROGRESS", meta={"step": "broll_collected", "progress": 100})
        
        return {
            "status": "completed",
            "video_project_id": video_project_id,
            "broll_count": len(broll)
        }
    
    except Exception as e:
        logger.error(f"Error en collect_broll_task: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True, name="tasks.render_video_task", max_retries=3)
def render_video_task(
    self,
    video_project_id: int,
    script_json: dict,
    audio_path: str,
    broll_videos: list,
    platform: str = "tiktok"
):
    """
    Tarea asincrónica principal: Renderizar video completo
    Esta es la tarea más pesada computacionalmente
    """
    try:
        self.update_state(state="PROGRESS", meta={
            "step": "starting_render",
            "progress": 0,
            "video_project_id": video_project_id
        })
        
        from modules_video_composer import get_video_composer
        from modules_subtitles import get_subtitle_generator
        import asyncio
        
        logger.info(f"Renderizando video para proyecto {video_project_id}")
        
        # Paso 1: Generar subtítulos sincronizados
        self.update_state(state="PROGRESS", meta={
            "step": "generating_subtitles",
            "progress": 20,
            "video_project_id": video_project_id
        })
        
        subtitle_gen = get_subtitle_generator(model="base")
        timestamps = asyncio.run(subtitle_gen.generate_subtitle_timestamps(
            audio_path=audio_path,
            language="es"
        ))
        
        if not timestamps:
            raise Exception("No se pudieron generar subtítulos")
        
        subtitle_config = subtitle_gen.generate_dynamic_subtitle_config(timestamps)
        
        # Paso 2: Componer video
        self.update_state(state="PROGRESS", meta={
            "step": "composing_video",
            "progress": 50,
            "video_project_id": video_project_id
        })
        
        composer = get_video_composer(platform=platform)
        output_path = f"/tmp/clips_virales/video_{video_project_id}.mp4"
        
        video_path = asyncio.run(composer.compose_video(
            audio_path=audio_path,
            broll_videos=broll_videos,
            subtitle_config=subtitle_config,
            script_json=script_json,
            output_path=output_path
        ))
        
        if not video_path:
            raise Exception("Falló la composición del video")
        
        # Paso 3: Subir a cloud storage (S3/GCS)
        self.update_state(state="PROGRESS", meta={
            "step": "uploading_to_storage",
            "progress": 80,
            "video_project_id": video_project_id
        })
        
        storage_url = asyncio.run(upload_to_cloud_storage(video_path, video_project_id))
        
        # Paso 4: Finalizar
        self.update_state(state="PROGRESS", meta={
            "step": "finalizing",
            "progress": 95,
            "video_project_id": video_project_id
        })
        
        # Limpiar archivos temporales
        composer.cleanup_temp_files()
        
        self.update_state(state="PROGRESS", meta={
            "step": "completed",
            "progress": 100,
            "video_project_id": video_project_id
        })
        
        return {
            "status": "completed",
            "video_project_id": video_project_id,
            "video_url": storage_url,
            "subtitle_config": subtitle_config
        }
    
    except Exception as e:
        logger.error(f"Error en render_video_task: {e}")
        
        # Reintentar con backoff
        try:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            self.update_state(state="FAILURE", meta={"error": str(e)})
            return {
                "status": "failed",
                "video_project_id": video_project_id,
                "error": str(e)
            }


async def upload_to_cloud_storage(video_path: str, video_id: int) -> str:
    """
    Subir video a S3 o GCS
    """
    try:
        if settings.aws_access_key_id:
            # Usar S3
            import boto3
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            
            key = f"videos/video_{video_id}.mp4"
            s3.upload_file(video_path, settings.aws_s3_bucket, key)
            url = f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
            
        elif settings.gcs_project_id:
            # Usar Google Cloud Storage
            from google.cloud import storage
            client = storage.Client(project=settings.gcs_project_id)
            bucket = client.bucket(settings.gcs_bucket)
            blob = bucket.blob(f"videos/video_{video_id}.mp4")
            blob.upload_from_filename(video_path)
            url = blob.public_url
        
        else:
            raise Exception("No se configuró almacenamiento en la nube")
        
        logger.info(f"Video subido a: {url}")
        return url
    
    except Exception as e:
        logger.error(f"Error subiendo a cloud storage: {e}")
        return None
