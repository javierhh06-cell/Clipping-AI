"""
Aplicación FastAPI Principal
Backend de Generador de Clips Virales Empresarial
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from config import settings
from database import Base, engine, get_db, SessionLocal
from modules_script_generator import get_script_generator
from modules_tts import get_tts_engine
from modules_broll import get_broll_manager
from modules_subtitles import get_subtitle_generator
from modules_video_composer import get_video_composer
from modules_oauth import get_oauth_manager, get_platform_publisher
from celery_config import (
    generate_script_task, generate_audio_task, collect_broll_task, render_video_task
)

# Configurar logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Crear tablas en BD
Base.metadata.create_all(bind=engine)

# Instancia de FastAPI
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API empresarial para generar y publicar clips virales con IA"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Verificar estado de la API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0"
    }


# ============================================================================
# GENERACIÓN DE VIDEOS - API PRINCIPAL
# ============================================================================

@app.post("/api/v1/videos/generate")
async def generate_video(
    topic: str,
    platform: str = "tiktok",
    tone: str = "viral",
    duration: int = 30,
    db: Session = Depends(get_db)
):
    """
    Generar un video viral completo
    Orquesta todo el flujo: guión -> audio -> B-Roll -> subtítulos -> renderizado
    """
    try:
        # TODO: Autenticar usuario
        user_id = 1  # Placeholder
        
        from database import VideoProject, VideoStatus, RenderJob
        
        # Validar entrada
        if not topic or len(topic) < 3:
            raise HTTPException(status_code=400, detail="Tema muy corto")
        if platform not in ["tiktok", "instagram", "youtube_shorts"]:
            raise HTTPException(status_code=400, detail="Plataforma no soportada")
        
        # Crear proyecto en BD
        project = VideoProject(
            user_id=user_id,
            title=f"Clip - {topic[:50]}",
            topic=topic,
            platform=platform,
            tone=tone,
            duration_seconds=duration,
            status=VideoStatus.GENERATING
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"Proyecto de video creado: {project.id}")
        
        # Paso 1: Generar guión
        script_task = generate_script_task.delay(
            project.id,
            topic,
            platform
        )
        
        # Crear registro de render job
        render_job = RenderJob(
            video_project_id=project.id,
            celery_task_id=script_task.id,
            status="queued",
            current_step="guion"
        )
        db.add(render_job)
        db.commit()
        
        return {
            "status": "queued",
            "project_id": project.id,
            "job_id": script_task.id,
            "message": "Video en cola para procesamiento",
            "track_url": f"/api/v1/videos/{project.id}/progress"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/videos/{video_id}/progress")
async def get_video_progress(video_id: int, db: Session = Depends(get_db)):
    """Obtener estado del renderizado del video"""
    try:
        from database import VideoProject, RenderJob
        from celery.result import AsyncResult
        
        project = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        render_job = db.query(RenderJob).filter(
            RenderJob.video_project_id == video_id
        ).first()
        
        if not render_job:
            return {
                "project_id": video_id,
                "status": "no_job",
                "progress": 0
            }
        
        # Obtener estado de Celery
        result = AsyncResult(render_job.celery_task_id)
        
        return {
            "project_id": video_id,
            "job_id": render_job.celery_task_id,
            "status": result.state,
            "progress": result.info.get("progress", 0) if result.info else 0,
            "current_step": render_job.current_step,
            "result_url": render_job.output_file_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo progreso: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Obtener detalles de un video"""
    try:
        from database import VideoProject
        
        project = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        return {
            "id": project.id,
            "title": project.title,
            "topic": project.topic,
            "platform": project.platform,
            "status": project.status,
            "video_url": project.video_url,
            "created_at": project.created_at,
            "completed_at": project.completed_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo video: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@app.get("/api/v1/videos")
async def list_user_videos(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Listar videos del usuario autenticado"""
    try:
        user_id = 1
        from database import VideoProject
        
        videos = db.query(VideoProject).filter(
            VideoProject.user_id == user_id
        ).offset(skip).limit(limit).all()
        
        return {
            "items": [
                {
                    "id": v.id,
                    "title": v.title,
                    "topic": v.topic,
                    "platform": v.platform,
                    "status": v.status,
                    "created_at": v.created_at
                } for v in videos
            ],
            "total": len(videos),
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error listando videos: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@app.delete("/api/v1/videos/{video_id}")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Eliminar un video"""
    try:
        from database import VideoProject
        
        project = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        db.delete(project)
        db.commit()
        
        return {"status": "deleted", "video_id": video_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando video: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


# ============================================================================
# AUTENTICACIÓN OAUTH2
# ============================================================================

@app.get("/api/v1/auth/{platform}/authorize")
async def authorize_platform(platform: str):
    """Iniciar flujo OAuth2 con plataforma social"""
    if platform not in ["youtube", "instagram", "tiktok"]:
        raise HTTPException(status_code=400, detail="Plataforma no soportada")
    
    try:
        oauth_manager = get_oauth_manager()
        import secrets
        state = secrets.token_urlsafe(32)
        
        url = oauth_manager.get_authorization_url(platform, state)
        
        return {
            "authorization_url": url,
            "state": state,
            "platform": platform
        }
    
    except Exception as e:
        logger.error(f"Error en autorización OAuth: {e}")
        raise HTTPException(status_code=500, detail="Error en autenticación")


# ============================================================================
# PUBLICACIÓN EN PLATAFORMAS
# ============================================================================

@app.post("/api/v1/videos/{video_id}/publish/{platform}")
async def publish_video(
    video_id: int,
    platform: str,
    db: Session = Depends(get_db)
):
    """Publicar video en plataforma social"""
    try:
        if platform not in ["youtube", "instagram", "tiktok"]:
            raise HTTPException(status_code=400, detail="Plataforma no soportada")
        
        from database import VideoProject, OAuthAccount
        
        project = db.query(VideoProject).filter(VideoProject.id == video_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        if not project.video_url:
            raise HTTPException(status_code=400, detail="El video no está listo")
        
        user_id = 1  # TODO: Autenticar usuario
        
        oauth_account = db.query(OAuthAccount).filter(
            (OAuthAccount.user_id == user_id) & (OAuthAccount.provider == platform)
        ).first()
        
        if not oauth_account:
            raise HTTPException(
                status_code=400,
                detail=f"No tienes {platform} vinculado. Conecta tu cuenta primero."
            )
        
        return {
            "status": "queued",
            "platform": platform,
            "message": f"Video enviado a {platform}. Puedes verificar el estado en tu cuenta."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publicando video: {e}")
        raise HTTPException(status_code=500, detail="Error al publicar")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
