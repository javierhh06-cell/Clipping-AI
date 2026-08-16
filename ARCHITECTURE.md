# 🏗️ Arquitectura del Sistema

Documentación técnica detallada de la arquitectura y componentes del Generador de Clips Virales.

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         Cliente Web / Mobile                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application Server                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Routes & Endpoints                                      │   │
│  │ - POST /api/v1/videos/generate                          │   │
│  │ - GET /api/v1/videos/{id}/progress                      │   │
│  │ - POST /api/v1/videos/{id}/publish/{platform}           │   │
│  │ - GET /api/v1/auth/{platform}/authorize                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────┬──────────────┬──────────────┬──────────────────────┘
           │              │              │
      (Database)      (Task Queue)   (Cloud APIs)
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌───────────────┐
    │PostgreSQL│   │  Redis   │   │  Google APIs  │
    │          │   │ (Broker) │   │  - Gemini     │
    │  Users   │   │          │   │  - YouTube    │
    │ Projects │   │ Celery   │   │  - Drive      │
    │  Videos  │   │ Results  │   └───────────────┘
    └──────────┘   └──────────┘
                        │
                        │ Celery Tasks
                        ▼
    ┌──────────────────────────────────────────┐
    │     Celery Workers (Parallelizable)      │
    │                                          │
    │  Queue: videos (Rendering)               │
    │  ┌─────────────────────────────────┐   │
    │  │ Task 1: Generate Script         │   │
    │  │ ↓                               │   │
    │  │ Task 2: Generate Audio          │   │
    │  │ ↓                               │   │
    │  │ Task 3: Collect B-Roll          │   │
    │  │ ↓                               │   │
    │  │ Task 4: Generate Subtitles      │   │
    │  │ ↓                               │   │
    │  │ Task 5: Compose Video           │   │
    │  │ ↓                               │   │
    │  │ Task 6: Upload to Cloud         │   │
    │  │ ↓                               │   │
    │  │ Task 7: Publish to Platforms    │   │
    │  └─────────────────────────────────┘   │
    └──────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   AWS    │  │  Google  │  │  Pexels  │
    │   S3     │  │   GCS    │  │   API    │
    │          │  │          │  │          │
    │ Storage  │  │ Storage  │  │ B-Roll   │
    │ for MP4  │  │ for MP4  │  │ Videos   │
    └──────────┘  └──────────┘  └──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼               ▼               ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ YouTube  │  │Instagram │  │  TikTok  │
    │  Shorts  │  │  Reels   │  │ Platform │
    │ (OAuth2) │  │ (OAuth2) │  │ (OAuth2) │
    └──────────┘  └──────────┘  └──────────┘
```

## 🔄 Flujo de Generación de Video

### 1. Request Inicial
```
User → FastAPI POST /api/v1/videos/generate
       {
         "topic": "5 hábitos de productividad",
         "platform": "tiktok",
         "tone": "viral",
         "duration": 30
       }
       ↓
       Create VideoProject (DRAFT)
       ↓
       Queue Task with Celery
       ↓
       Return {status: "queued", project_id, job_id}
```

### 2. Generación en Paralelo (Workers)

```
├─ Worker 1: Generate Script (Gemini/GPT-4o)
│  ├─ Input: Topic, Platform, Duration, Tone
│  ├─ Output: {
│  │    "hook": {...},
│  │    "body": [...],
│  │    "cta": {...},
│  │    "metadata": {...}
│  │  }
│  └─ Store: script_json in DB
│
├─ Worker 2: Generate Audio (ElevenLabs/Coqui)
│  ├─ Input: Narration text from script
│  ├─ Process: TTS synthesis
│  ├─ Output: audio.mp3 + word timestamps
│  └─ Store: S3/GCS + URL in DB
│
└─ Worker 3: Collect B-Roll (Pexels API)
   ├─ Input: Keywords from script
   ├─ Process: Search and download videos
   ├─ Output: List of video files/URLs
   └─ Store: B-Roll metadata in DB
```

### 3. Procesamiento Secuencial (Post Paralelo)

```
Script + Audio + B-Roll Ready
       ↓
Generate Subtitles (OpenAI Whisper)
├─ Input: audio.mp3
├─ Extract: Word-level timestamps
├─ Output: [{word, start_ms, end_ms, confidence}]
└─ Store: subtitles_json in DB
       ↓
Compose Video (MoviePy)
├─ Compile B-Roll clips to duration
├─ Layer audio track
├─ Add dynamic subtitles with animations
├─ Apply effects and transitions
├─ Output: video.mp4 (platform-specific resolution)
└─ Store: video_url in DB
       ↓
Upload to Cloud Storage (S3/GCS)
├─ Upload MP4 file
├─ Generate CDN URL
└─ Store: video_url, thumbnail_url in DB
       ↓
Mark VideoProject as COMPLETED
```

### 4. Publicación Automática

```
For Each Connected Platform (OAuth2):
  ├─ YouTube: Upload with video metadata
  │  └─ Extract from script, store external_id
  │
  ├─ Instagram: Create Reel draft
  │  └─ 9:16 aspect ratio, caption from title
  │
  └─ TikTok: Send to user's drafts
     └─ User must publish manually
```

## 🗄️ Estructura de Base de Datos

### Tablas Principales

```sql
-- Usuarios y Autenticación
users
├── id (PK)
├── email (UNIQUE)
├── username (UNIQUE)
├── hashed_password
├── is_active
├── created_at

oauth_accounts
├── id (PK)
├── user_id (FK → users)
├── provider (ENUM: youtube, instagram, tiktok)
├── access_token
├── refresh_token
├── token_expires_at
└── account_info (JSON)

-- Proyectos de Video
video_projects
├── id (PK)
├── user_id (FK → users)
├── title
├── topic
├── platform (ENUM)
├── tone
├── duration_seconds
├── status (ENUM: draft, generating, rendering, completed, failed)
├── script_json (JSON)
├── audio_url
├── video_url
├── thumbnail_url
├── subtitles_json (JSON)
├── broll_metadata (JSON)
├── published_on (JSON: {youtube_id, instagram_id, tiktok_id})
└── created_at, updated_at, completed_at

-- Trabajos de Renderizado
render_jobs
├── id (PK)
├── video_project_id (FK)
├── celery_task_id
├── status (ENUM: queued, processing, completed, failed)
├── progress_percentage
├── current_step (enum: guion, audio, broll, subs, render, upload)
├── output_file_url
└── error_message

-- Notificaciones y Logs
notifications
├── id (PK)
├── user_id (FK)
├── title
├── message
└── read_at

api_usage_logs
├── id (PK)
├── user_id (FK)
├── api_name (google_gemini, elevenlabs, pexels, etc.)
├── tokens_used
├── cost (en centavos)
└── created_at
```

## 🔌 Integración de APIs Externas

### 1. Generación de Guiones

#### Google Gemini API
```python
# Endpoint: generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent
# Method: POST
# Auth: API Key

Request:
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Genera un guión para TikTok sobre productividad..."}
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 2048
  }
}

Response:
{
  "candidates": [
    {
      "content": {
        "parts": [
          {"text": "{...JSON guión...}"}
        ]
      }
    }
  ]
}
```

#### OpenAI GPT-4o
```python
# Endpoint: api.openai.com/v1/chat/completions
# Method: POST
# Auth: Bearer token

Request:
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "Eres un experto en guiones virales..."},
    {"role": "user", "content": "Genera un guión para TikTok..."}
  ],
  "response_format": {"type": "json_object"},
  "temperature": 0.7
}
```

### 2. Síntesis de Voz

#### ElevenLabs API
```python
# Endpoint: api.elevenlabs.io/v1/text-to-speech/{voice_id}
# Method: POST
# Auth: xi-api-key header

Request:
{
  "text": "Texto a sintetizar",
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.8
  }
}

Response: Binary MP3 audio
```

### 3. B-Roll / Stock Videos

#### Pexels API
```python
# Endpoint: api.pexels.com/v1/videos/search
# Method: GET
# Auth: Authorization header

Request:
GET /v1/videos/search?query=parkour&per_page=15&min_duration=1&max_duration=20

Response:
{
  "videos": [
    {
      "id": 123456,
      "url": "https://...",
      "width": 1280,
      "height": 720,
      "duration": 10,
      "video_files": [{...}],
      "user": {...}
    }
  ],
  "total_results": 150
}
```

### 4. Subtítulos / Transcripción

#### OpenAI Whisper (Local)
```python
import whisper

model = whisper.load_model("base")  # Local processing
result = model.transcribe("audio.mp3", language="es")

# result["segments"][0] = {
#   "start": 0.0,
#   "end": 2.5,
#   "text": "Hola mundo",
#   "words": [
#     {"word": "Hola", "start": 0.0, "end": 1.2, "confidence": 0.98},
#     {"word": "mundo", "start": 1.3, "end": 2.5, "confidence": 0.97}
#   ]
# }
```

### 5. Publicación en Plataformas

#### YouTube Data API v3
```python
# Endpoint: youtube.googleapis.com/youtube/v3/videos
# Method: POST
# Auth: OAuth2 access_token

# Requiere multipart upload para el archivo de video
# Documentación: https://developers.google.com/youtube/v3/guides/using_the_api
```

#### Instagram Graph API
```python
# Endpoint: graph.instagram.com/v18.0/{user_id}/media
# Method: POST
# Auth: OAuth2 access_token

Request:
{
  "media_type": "REELS",
  "video_url": "https://...",
  "caption": "Caption del video"
}
```

#### TikTok Content Posting API
```python
# Endpoint: open.tiktokapis.com/v1/post/publish/action/upload/
# Method: POST
# Auth: OAuth2 access_token

# TikTok envía el video a la bandeja de entrada del usuario
# El usuario debe publicarlo manualmente
```

## 🚀 Performance y Escalabilidad

### Concurrencia Celery
```
Configuración actual:
- Max 2 workers renderizando videos simultáneamente
- Pool: prefork (recomendado para CPU-bound tasks)
- Worker prefetch: 1 (evita sobrecarga)

Para escalar:
- Aumentar --concurrency=N en docker-compose.yml
- Usar múltiples máquinas con docker-compose up --scale
- Implementar task routing por prioridad
```

### Optimizaciones de Renderizado
```
MoviePy Settings:
- codec: libx264 (fast) o libx265 (better quality)
- preset: fast (balance speed/quality)
- threads: 4 (ajustable según CPU)
- bitrate: 6000k-10000k (según plataforma)
- fps: 30 (TikTok/Instagram) o 60 (YouTube)
```

### Caching y CDN
```
CloudFront (AWS):
- Cache videos generados
- TTL: 30 días para videos completados
- Invalidar cache solo si se elimina proyecto

Google Cloud CDN:
- Integración automática con GCS
- Cache hit ratio: ~80%
```

## 🔐 Seguridad

### Autenticación y Autorización
```python
# JWT Tokens
- Access Token: 30 minutos
- Refresh Token: 7 días
- Stored securely in httponly cookies
- CSRF protection enabled

# OAuth2 Flows
- Authorization Code Flow (más seguro)
- Refresh tokens rotados automáticamente
- Token expiration checking antes de usar
```

### Validación de Entrada
```python
# Pydantic Models
- Type checking en todos los endpoints
- String length limits
- Enum restrictions
- Email validation

# Rate Limiting
- 100 requests/minute por usuario
- 1000 requests/hour globales
- Queue job rate limiting
```

### Encriptación
```
- Passwords: bcrypt (12 rounds)
- API Keys en .env (no en código)
- Database: SSL connection
- S3/GCS: server-side encryption
- OAuth2 tokens: encrypted in DB
```

## 📊 Monitoreo y Observabilidad

### Métricas
```
Flower Dashboard:
- Tasks per minute
- Worker status
- Task success/failure rates
- Processing times

Application Metrics:
- Request latency (p50, p95, p99)
- Error rates por endpoint
- Database query times
- File upload/download speeds
```

### Logging
```python
# Python logging
- All modules use logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR

# CloudWatch Integration (AWS)
- Send logs to CloudWatch
- Alerts on errors
- Log retention: 30 days
```

### Health Checks
```python
GET /health
Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "environment": "production",
  "version": "1.0.0"
}
```

## 🔄 Flujo de Errores y Recuperación

### Reintentos Automáticos
```python
Celery Tasks:
- Retry count: 3
- Retry delay: 60, 120, 240 segundos (exponential backoff)
- Task timeout: 3600 segundos (1 hora)
- Soft timeout: 3300 segundos

Errores No Recuperables:
- Invalid API keys
- Unsupported formats
- Quota exceeded
→ Mark as FAILED, notificar usuario
```

### Fallback Mechanisms
```python
If Gemini fails → Use GPT-4o
If ElevenLabs fails → Use Coqui local TTS
If S3 fails → Retry con GCS
If video rendering fails → Store error, retry con diferentes settings
```

## 📦 Deployment

### Docker Compose Stack
```yaml
Services:
1. PostgreSQL (Master database)
2. Redis (Message broker + result backend)
3. FastAPI (Web server, uvicorn 4 workers)
4. Celery Worker (2 concurrent video renders)
5. Flower (Monitoring dashboard)

Resource Limits:
- PostgreSQL: 512MB RAM, 2 CPU
- Redis: 256MB RAM, 1 CPU
- FastAPI: 1GB RAM, 2 CPU
- Celery Worker: 4GB RAM, 4 CPU (adjustable)
```

### Production Checklist
```
□ SSL/TLS certificates (Let's Encrypt)
□ Environment variables from secrets manager
□ Database backups automated (daily)
□ Log centralization (CloudWatch/DataDog)
□ Monitoring and alerting configured
□ Rate limiting enabled
□ CORS properly restricted
□ Sensitive headers removed
□ API versioning (v1, v2, etc.)
□ Documentation up to date
□ Load testing completed (k6, JMeter)
□ Security audit passed
```

---

**Actualizado**: Enero 2024
**Version**: 1.0.0
