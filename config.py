"""
Configuración centralizada de la aplicación
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    
    # ========== Base de Datos ==========
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/clips_db")
    
    # ========== Redis & Celery ==========
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    
    # ========== APIs LLM ==========
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # ========== TTS ==========
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    # ========== B-Roll ==========
    pexels_api_key: str = os.getenv("PEXELS_API_KEY", "")
    
    # ========== Cloud Storage ==========
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_s3_bucket: str = os.getenv("AWS_S3_BUCKET", "clips-virales")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    
    gcs_project_id: str = os.getenv("GCS_PROJECT_ID", "")
    gcs_bucket: str = os.getenv("GCS_BUCKET", "")
    
    # ========== OAuth2 Security ==========
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # ========== OAuth2 Providers ==========
    youtube_client_id: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    youtube_client_secret: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    youtube_redirect_uri: str = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback")
    
    instagram_client_id: str = os.getenv("INSTAGRAM_CLIENT_ID", "")
    instagram_client_secret: str = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
    instagram_redirect_uri: str = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/auth/instagram/callback")
    
    tiktok_client_id: str = os.getenv("TIKTOK_CLIENT_ID", "")
    tiktok_client_secret: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    tiktok_redirect_uri: str = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/auth/tiktok/callback")
    
    # ========== Application Settings ==========
    app_name: str = "Generador de Clips Virales"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # ========== FFmpeg ==========
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    ffprobe_path: str = os.getenv("FFPROBE_PATH", "ffprobe")
    
    # ========== Processing ==========
    max_video_duration_seconds: int = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "300"))
    max_concurrent_renders: int = int(os.getenv("MAX_CONCURRENT_RENDERS", "3"))
    temp_files_dir: str = os.getenv("TEMP_FILES_DIR", "/tmp/clips_virales")
    
    # ========== Platform Limits ==========
    youtube_max_file_size_mb: int = int(os.getenv("YOUTUBE_MAX_FILE_SIZE_MB", "5000"))
    instagram_max_file_size_mb: int = int(os.getenv("INSTAGRAM_MAX_FILE_SIZE_MB", "4000"))
    tiktok_max_file_size_mb: int = int(os.getenv("TIKTOK_MAX_FILE_SIZE_MB", "287"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
