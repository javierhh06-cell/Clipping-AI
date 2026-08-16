"""
Esquemas Pydantic para validación de requests y responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# USUARIOS
# ============================================================================

class UserCreate(BaseModel):
    """Request para crear usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Response de usuario"""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# VIDEOS
# ============================================================================

class VideoCreateRequest(BaseModel):
    """Request para crear un video"""
    topic: str = Field(..., min_length=5, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    platform: str = Field(..., regex="^(tiktok|instagram|youtube_shorts)$")
    tone: str = Field("viral", regex="^(viral|educativo|cómico|motivacional)$")
    duration: int = Field(30, ge=15, le=300)


class VideoResponseDTO(BaseModel):
    """Response de video"""
    id: int
    title: str
    topic: str
    platform: str
    status: str
    video_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VideoProgressResponse(BaseModel):
    """Response del progreso de video"""
    project_id: int
    job_id: str
    status: str
    progress: int
    current_step: Optional[str]
    result_url: Optional[str]


# ============================================================================
# GUIONES
# ============================================================================

class ScriptGenerateRequest(BaseModel):
    """Request para generar guión"""
    topic: str
    platform: str = "tiktok"
    duration: int = 30
    tone: str = "viral"
    additional_context: Optional[str] = None


class ScriptHook(BaseModel):
    """Hook del guión"""
    text: str
    visual_cue: str


class ScriptBodySection(BaseModel):
    """Sección del body del guión"""
    narration: str
    visual_description: str
    duration_seconds: int
    broll_keywords: List[str]
    visual_effects: List[str]


class ScriptCTA(BaseModel):
    """Call-to-action del guión"""
    text: str
    visual_cue: str


class ScriptMetadata(BaseModel):
    """Metadata del guión"""
    total_duration: int
    platform: str
    tone: str
    target_audience: str
    key_keywords: List[str]
    hashtags: List[str]
    music_suggestions: List[str]


class ScriptResponse(BaseModel):
    """Guión completo generado"""
    hook: ScriptHook
    body: List[ScriptBodySection]
    cta: ScriptCTA
    metadata: ScriptMetadata
    production_tips: List[str]


# ============================================================================
# AUDIO / TTS
# ============================================================================

class AudioGenerateRequest(BaseModel):
    """Request para generar audio"""
    text: str
    language: str = "es-ES"
    gender: str = "femenino"


class WordTimestamp(BaseModel):
    """Timestamp de palabra"""
    word: str
    start_ms: int
    end_ms: int
    confidence: float


class AudioWithTimestampsResponse(BaseModel):
    """Response de audio con timestamps"""
    audio_path: str
    duration_ms: int
    word_timestamps: List[WordTimestamp]
    text: str


# ============================================================================
# B-ROLL
# ============================================================================

class BRollVideo(BaseModel):
    """Información de video B-Roll"""
    source: str  # "pexels", "internal"
    id: str
    url: str
    duration: int
    tags: List[str]
    width: Optional[int]
    height: Optional[int]
    photographer: Optional[str]


class BRollSearchResponse(BaseModel):
    """Response de búsqueda de B-Roll"""
    keywords: List[str]
    results: List[BRollVideo]
    total: int


# ============================================================================
# SUBTÍTULOS
# ============================================================================

class SubtitleFrame(BaseModel):
    """Frame de subtítulo"""
    start_ms: int
    end_ms: int
    text: str
    is_keyword: bool
    animation: str
    color_override: Optional[str]


class SubtitleConfig(BaseModel):
    """Configuración de subtítulos dinámicos"""
    font_family: str = "Arial"
    font_size: int = 48
    primary_color: str = "#FFFFFF"
    highlight_color: str = "#FF1493"
    position: str = "bottom_center"
    animation: str = "fade"
    frames: List[SubtitleFrame]


# ============================================================================
# PUBLICACIÓN
# ============================================================================

class PublishToResponse(BaseModel):
    """Response de publicación"""
    status: str
    platform: str
    message: str
    video_id: Optional[str]
    url: Optional[str]


# ============================================================================
# OAUTH2
# ============================================================================

class OAuthTokenResponse(BaseModel):
    """Response de token OAuth2"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int]


class OAuthAuthorizationResponse(BaseModel):
    """Response de autorización OAuth2"""
    authorization_url: str
    state: str
    platform: str


# ============================================================================
# ANÁLISIS Y ESTADÍSTICAS
# ============================================================================

class VideoStatsResponse(BaseModel):
    """Estadísticas de video"""
    total_videos: int
    total_storage_used_mb: float
    average_generation_time_seconds: float
    success_rate_percent: float
    most_used_platform: str
    most_used_tone: str


class UserStatsResponse(BaseModel):
    """Estadísticas del usuario"""
    total_generated_videos: int
    videos_by_platform: Dict[str, int]
    videos_by_status: Dict[str, int]
    api_calls_this_month: int
    storage_used_mb: float
