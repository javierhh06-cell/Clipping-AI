"""
Configuración de Base de Datos con SQLAlchemy
Modelos de ORM para la aplicación
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import enum
from config import settings

# Crear engine
engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


# Dependency para obtener DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# MODELOS
# ============================================================================

class User(Base):
    """Modelo de usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("VideoProject", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class OAuthProviderEnum(str, enum.Enum):
    """Proveedores OAuth"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE = "google"


class OAuthAccount(Base):
    """Cuentas OAuth conectadas"""
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(OAuthProviderEnum), nullable=False)
    provider_user_id = Column(String, nullable=False)
    provider_username = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scope = Column(String, nullable=True)
    account_info = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="oauth_accounts")
    
    def __repr__(self):
        return f"<OAuthAccount {self.provider}>"


class VideoStatus(str, enum.Enum):
    """Estados de video"""
    DRAFT = "draft"
    GENERATING = "generating"
    PROCESSING = "processing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


class PlatformEnum(str, enum.Enum):
    """Plataformas soportadas"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class VideoProject(Base):
    """Proyecto de video"""
    __tablename__ = "video_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    platform = Column(Enum(PlatformEnum), nullable=False)
    tone = Column(String, default="viral")
    duration_seconds = Column(Integer, default=30)
    
    script_json = Column(JSON, nullable=True)
    audio_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    subtitles_json = Column(JSON, nullable=True)
    broll_metadata = Column(JSON, nullable=True)
    
    status = Column(Enum(VideoStatus), default=VideoStatus.DRAFT)
    error_message = Column(Text, nullable=True)
    
    published_on = Column(JSON, nullable=True)
    external_ids = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="videos")
    render_jobs = relationship("RenderJob", back_populates="video_project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VideoProject {self.title}>"


class RenderJobStatus(str, enum.Enum):
    """Estados del trabajo de renderizado"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderJob(Base):
    """Trabajo de renderizado Celery"""
    __tablename__ = "render_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    video_project_id = Column(Integer, ForeignKey("video_projects.id"), nullable=False)
    
    celery_task_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(RenderJobStatus), default=RenderJobStatus.QUEUED)
    
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String, nullable=True)
    
    output_file_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    video_project = relationship("VideoProject", back_populates="render_jobs")
    
    def __repr__(self):
        return f"<RenderJob {self.celery_task_id}>"


class NotificationStatus(str, enum.Enum):
    """Estados de notificación"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    """Sistema de notificaciones"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="info")
    
    related_video_id = Column(Integer, ForeignKey("video_projects.id"), nullable=True)
    
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Notification {self.title}>"


class APIUsageLog(Base):
    """Registro de uso de APIs"""
    __tablename__ = "api_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    api_name = Column(String, nullable=False)
    video_project_id = Column(Integer, nullable=True)
    
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)
    
    request_metadata = Column(JSON, nullable=True)
    response_status = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIUsageLog {self.api_name}>"
    """Modelo de usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable para OAuth
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("VideoProject", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class OAuthProviderEnum(str, enum.Enum):
    """Proveedores OAuth soportados"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE = "google"


class OAuthAccount(Base):
    """Almacenamiento de cuentas OAuth conectadas"""
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(OAuthProviderEnum), nullable=False)
    provider_user_id = Column(String, nullable=False)
    provider_username = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scope = Column(String, nullable=True)
    account_info = Column(JSON, nullable=True)  # Info adicional del usuario en la plataforma
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="oauth_accounts")
    
    __table_args__ = (
        # Unique constraint: un usuario no puede conectar la misma plataforma dos veces
    )
    
    def __repr__(self):
        return f"<OAuthAccount {self.provider} - {self.provider_username}>"


class VideoStatus(str, enum.Enum):
    """Estados posibles de un video"""
    DRAFT = "draft"
    GENERATING = "generating"
    PROCESSING = "processing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    PUBLISHED = "published"


class PlatformEnum(str, enum.Enum):
    """Plataformas soportadas"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class VideoProject(Base):
    """Proyecto de video generado"""
    __tablename__ = "video_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información básica
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuración
    platform = Column(Enum(PlatformEnum), nullable=False)
    tone = Column(String, default="viral")  # viral, educativo, cómico, motivacional
    duration_seconds = Column(Integer, default=30)
    
    # Contenido generado
    script_json = Column(JSON, nullable=True)  # Guión completo en JSON
    audio_url = Column(String, nullable=True)  # URL de audio sintetizado
    video_url = Column(String, nullable=True)  # URL del video final renderizado
    thumbnail_url = Column(String, nullable=True)  # Thumbnail del video
    
    # Subtítulos y metadata
    subtitles_json = Column(JSON, nullable=True)  # Subtítulos sincronizados con timestamps
    broll_metadata = Column(JSON, nullable=True)  # Información de B-Roll utilizado
    
    # Estado y procesamiento
    status = Column(Enum(VideoStatus), default=VideoStatus.DRAFT)
    error_message = Column(Text, nullable=True)
    
    # Publicación
    published_on = Column(JSON, nullable=True)  # Plataformas donde está publicado
    external_ids = Column(JSON, nullable=True)  # IDs externos (video_id de YouTube, etc.)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relaciones
    user = relationship("User", back_populates="videos")
    render_jobs = relationship("RenderJob", back_populates="video_project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VideoProject {self.title}>"


class RenderJobStatus(str, enum.Enum):
    """Estados del trabajo de renderizado"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderJob(Base):
    """Trabajo de renderizado en Celery"""
    __tablename__ = "render_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    video_project_id = Column(Integer, ForeignKey("video_projects.id"), nullable=False)
    
    celery_task_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(RenderJobStatus), default=RenderJobStatus.QUEUED)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String, nullable=True)  # "guion", "audio", "broll", "subs", "render", "upload"
    
    # Resultados
    output_file_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relación
    video_project = relationship("VideoProject", back_populates="render_jobs")
    
    def __repr__(self):
        return f"<RenderJob {self.celery_task_id} - {self.status}>"


class NotificationStatus(str, enum.Enum):
    """Estados de notificación"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    """Sistema de notificaciones para usuarios"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="info")  # info, success, warning, error
    
    related_video_id = Column(Integer, ForeignKey("video_projects.id"), nullable=True)
    
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Notification {self.title}>"


class APIUsageLog(Base):
    """Registro de uso de APIs para tracking y facturación"""
    __tablename__ = "api_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    api_name = Column(String, nullable=False)  # "google_gemini", "elevenlabs", "pexels", etc.
    video_project_id = Column(Integer, nullable=True)
    
    tokens_used = Column(Integer, nullable=True)  # Para APIs basadas en tokens
    cost = Column(Integer, nullable=True)  # En centavos
    
    request_metadata = Column(JSON, nullable=True)
    response_status = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIUsageLog {self.api_name}>"
