# 🎬 Generador Empresarial de Clips Virales con IA

Sistema **production-ready** para generar, renderizar y publicar clips virales automáticamente en YouTube, Instagram y TikTok usando inteligencia artificial avanzada.

## 🚀 Características Principales

### 1. **Generador de Guiones Inteligente** (LLM)
- ✨ Soporta **Google Gemini 1.5 Pro** y **OpenAI GPT-4o**
- 📋 Genera guiones en **formato JSON estructurado**
- 🎯 Optimización por plataforma (TikTok, Instagram, YouTube Shorts)
- 🎭 Múltiples tonos: viral, educativo, cómico, motivacional
- 🔄 Generación de variantes para A/B testing

### 2. **Motor de Voz Premium** (TTS)
- 🎙️ **ElevenLabs** para voces ultra realistas y emotivas
- 🌍 Soporte multiidioma: Español (ES, MX, AR)
- ⚡ Coqui TTS como alternativa open-source
- 🎵 Timestamps de palabras con OpenAI Whisper

### 3. **Recolector de B-Roll Inteligente**
- 📸 Integración con **Pexels API** para multimedia premium
- 🎮 Repositorio interno de loops (GTA V parkour, Minecraft, etc.)
- ☁️ Almacenamiento en Google Cloud Storage / AWS S3
- 🏷️ Búsqueda semántica de B-Roll por keywords

### 4. **Subtítulos Dinámicos Sincronizados**
- ⏱️ **Timestamps precisos a nivel de palabra** con Whisper
- 🎨 Animaciones dinámicas (fade, pop, slide, bounce)
- 🌈 Colorización de palabras clave para máxima viralidad
- 📝 Exporta SRT, VTT y configuración JSON

### 5. **Compositor de Video Profesional**
- 🎞️ **MoviePy + FFmpeg** para máxima calidad y velocidad
- 🔗 Orquestación de B-Roll, audio y subtítulos
- 📐 Resoluciones optimizadas por plataforma (9:16 vertical)
- ✂️ Transiciones suaves, fades y efectos
- 🚀 Renderizado paralelo con Celery

### 6. **Publicación Automática con OAuth2**
- 📤 **YouTube Shorts**: Subida directa a canal del usuario
- 📱 **Instagram Reels**: Publicación automática (relación 9:16)
- 🎵 **TikTok**: Direct Post a la bandeja de entrada del usuario
- 🔑 Gestión segura de tokens OAuth2 y refresh automático
- 📊 Tracking de videos publicados

### 7. **Infraestructura Enterprise**
- **FastAPI** backend con arquitectura modular
- **PostgreSQL** para persistencia de datos
- **Redis + Celery** para procesamiento asincrónico
- **Docker + Docker Compose** para deploy inmediato
- 📈 Flower dashboard para monitoreo de Celery
- 🔐 Autenticación segura y gestión de permisos

## 📋 Requisitos Previos

### Dependencias de Sistemas
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsndfile1 libopus0 python3.11-dev

# macOS
brew install ffmpeg python@3.11

# Windows
# Descargar FFmpeg desde https://ffmpeg.org/download.html
```

### Cuentas y APIs Necesarias
1. **Google Cloud** - Gemini API y YouTube Data API v3
2. **OpenAI** - GPT-4o (opcional, alternativa a Gemini)
3. **ElevenLabs** - TTS premium (o usar Coqui open-source)
4. **Pexels** - API para stock de videos
5. **AWS S3** o **Google Cloud Storage** - Almacenamiento de videos
6. **YouTube, Instagram, TikTok** - Aplicaciones OAuth2 registradas

## ⚙️ Instalación

### Opción 1: Docker Compose (Recomendado)

```bash
# Clonar repositorio
git clone https://github.com/tuusuario/clips-virales.git
cd clips-virales

# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus claves API
nano .env

# Lanzar contenedores
docker-compose up -d

# Verificar
curl http://localhost:8000/health
# Flower dashboard: http://localhost:5555
```

### Opción 2: Instalación Local

```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # o `venv\Scripts\activate` en Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus configuraciones

# Inicializar base de datos
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Iniciar Redis y PostgreSQL (localmente o con Docker)
# Redis: docker run -d -p 6379:6379 redis:7
# PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Iniciar Celery Worker (terminal 1)
celery -A celery_config worker -l info

# Iniciar FastAPI (terminal 2)
uvicorn app:app --reload --port 8000
```

## 🎯 Uso de la API

### 1. Generar un Video Viral

```bash
curl -X POST "http://localhost:8000/api/v1/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "5 hábitos de productividad para profesionales",
    "platform": "tiktok",
    "tone": "viral",
    "duration": 30
  }'
```

**Response:**
```json
{
  "status": "queued",
  "project_id": 1,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Video en cola para procesamiento",
  "track_url": "/api/v1/videos/1/progress"
}
```

### 2. Monitorear Progreso

```bash
curl "http://localhost:8000/api/v1/videos/1/progress"
```

**Response:**
```json
{
  "project_id": 1,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PROGRESS",
  "progress": 65,
  "current_step": "rendering",
  "result_url": "https://s3.amazonaws.com/clips-virales/videos/video_1.mp4"
}
```

### 3. Obtener Detalles del Video

```bash
curl "http://localhost:8000/api/v1/videos/1"
```

### 4. Publicar en Plataforma

```bash
curl -X POST "http://localhost:8000/api/v1/videos/1/publish/youtube"
```

### 5. Listar Videos del Usuario

```bash
curl "http://localhost:8000/api/v1/videos?skip=0&limit=20"
```

## 🔐 Autenticación OAuth2

### Conectar YouTube

```bash
# Obtener URL de autorización
curl "http://localhost:8000/api/v1/auth/youtube/authorize"

# Response contiene URL para que el usuario autorice
# Después de autorizar, se guarda el token automáticamente
```

### Conectar Instagram y TikTok

Mismo proceso que YouTube, pero con endpoints:
- `/api/v1/auth/instagram/authorize`
- `/api/v1/auth/tiktok/authorize`

## 📁 Estructura del Proyecto

```
clips-virales/
├── app.py                      # FastAPI principal
├── config.py                   # Configuración centralizada
├── database.py                 # Modelos SQLAlchemy
├── celery_config.py           # Configuración de Celery y tareas
├── models_schemas.py          # Esquemas Pydantic
│
├── modules/
│   ├── modules_script_generator.py    # Generador de guiones (Gemini/GPT-4o)
│   ├── modules_tts.py                 # TTS (ElevenLabs/Coqui)
│   ├── modules_broll.py               # Recolector B-Roll (Pexels)
│   ├── modules_subtitles.py           # Subtítulos sincronizados (Whisper)
│   ├── modules_video_composer.py      # Compositor de video (MoviePy)
│   └── modules_oauth.py               # OAuth2 y publicación
│
├── docker-compose.yml         # Orquestación de contenedores
├── Dockerfile                 # API container
├── Dockerfile.celery         # Celery worker container
├── requirements.txt          # Dependencias Python
├── .env.example             # Template de configuración
└── README.md                # Este archivo
```

## 🔌 Configuración de APIs

### Google Gemini

```bash
# 1. Ir a https://aistudio.google.com
# 2. Crear API Key
# 3. En .env:
GOOGLE_API_KEY=your_key_here
```

### OpenAI GPT-4o

```bash
# 1. Ir a https://platform.openai.com/account/api-keys
# 2. Crear API Key
# 3. En .env:
OPENAI_API_KEY=sk-...
```

### ElevenLabs TTS

```bash
# 1. Ir a https://elevenlabs.io
# 2. Crear API Key
# 3. En .env:
ELEVENLABS_API_KEY=your_key_here
```

### Pexels API

```bash
# 1. Ir a https://www.pexels.com/api/
# 2. Crear API Key
# 3. En .env:
PEXELS_API_KEY=your_key_here
```

### AWS S3

```bash
# En .env:
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=clips-virales-prod
AWS_REGION=us-east-1
```

### YouTube OAuth2

```bash
# 1. Google Cloud Console > Crear proyecto
# 2. APIs > YouTube Data API v3 > Habilitar
# 3. Credenciales > OAuth 2.0 > Crear credenciales
# 4. En .env:
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
```

## 🎬 Flujo de Generación de Video

```
1. Usuario solicita nuevo video
   ↓
2. PARALELO:
   - Generar guión con LLM (Gemini/GPT-4o)
   - Extraer keywords para B-Roll
   
3. PARALELO (mientras se genera guión):
   - Sintetizar audio con TTS (ElevenLabs)
   - Recolectar B-Roll (Pexels API)
   
4. SECUENCIAL (después de guión + audio):
   - Generar subtítulos con Whisper
   - Sincronizar timestamps de palabras
   
5. COMPOSITOR DE VIDEO:
   - Compilar B-Roll en secuencia
   - Superponer audio
   - Agregar subtítulos dinámicos
   - Aplicar efectos y transiciones
   
6. RENDERIZADO:
   - Exportar MP4 optimizado para plataforma
   - Subir a S3/GCS
   
7. PUBLICACIÓN:
   - Publicar automáticamente en YouTube/Instagram/TikTok
   - Almacenar metadatos y URLs externas

8. NOTIFICACIÓN:
   - Enviar notificación al usuario
   - Video listo para usar
```

## 📊 Monitoreo y Estadísticas

### Flower Dashboard
Acceder a `http://localhost:5555` para monitorear:
- Workers activos
- Tareas en cola
- Histórico de ejecución
- Tiempos de procesamiento

### Logs
```bash
# Logs de FastAPI
docker logs clips_api -f

# Logs de Celery Worker
docker logs clips_celery_worker -f

# Logs de PostgreSQL
docker logs clips_db -f
```

## 🐛 Solución de Problemas

### "GOOGLE_API_KEY not found"
- Verifica que .env existe y contiene `GOOGLE_API_KEY=`
- No dejes espacios alrededor del `=`

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep clips_db

# Reiniciar servicios
docker-compose restart db api
```

### Celery tasks no se ejecutan
```bash
# Verificar Redis
docker exec clips_redis redis-cli ping

# Ver logs del worker
docker logs clips_celery_worker -f

# Reiniciar worker
docker-compose restart celery_worker
```

### Problemas con FFmpeg
```bash
# Instalar FFmpeg
sudo apt-get install ffmpeg

# Verificar instalación
ffmpeg -version
```

## 📈 Optimizaciones y Escalabilidad

### Aumentar Concurrencia de Rendering
```bash
# En docker-compose.yml, aumentar workers:
command: celery -A celery_config worker -l info -Q videos --concurrency=8
```

### Usar múltiples workers
```bash
# Lanzar múltiples instancias de worker
docker-compose up -d --scale celery_worker=4
```

### Configurar S3 para mayor throughput
```env
# En .env
AWS_REGION=us-east-1  # Seleccionar región cercana
```

## 🚀 Deploy en Producción

### Heroku
```bash
heroku login
heroku create tu-app-clips
git push heroku main
```

### AWS ECS
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag clips-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/clips-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/clips-api:latest
```

### Google Cloud Run
```bash
gcloud run deploy clips-api --source . --platform managed --region us-central1
```

## 📝 Ejemplos de Temas Virales

### Productividad
- "5 hábitos de productividad que cambiarán tu vida"
- "Rutina matinal de 10 minutos para ser más eficiente"
- "Técnica Pomodoro explicada en 30 segundos"

### Educación
- "Cómo aprender un idioma en 100 días"
- "Los 3 errores que cometes estudiando"
- "Carrera en tecnología: guía completa"

### Lifestyle
- "Recetas saludables que puedes hacer en 5 minutos"
- "Ejercicios sin equipo para hacer en casa"
- "Tips de meditación para reducir estrés"

## 💡 Tips para Máxima Viralidad

1. **Gancho en 3 segundos**: Captar atención inmediatamente
2. **Subtítulos dinámicos**: Las palabras clave deben resaltar
3. **B-Roll de calidad**: Videos satisfactorios y aesthetic
4. **Audio de calidad**: Voz clara y música de fondo adecuada
5. **Hashtags relevantes**: Usar trending en cada plataforma
6. **Variantes A/B**: Generar 3 versiones y probar cuál funciona mejor

## 📞 Soporte

Para preguntas, bugs o sugerencias:
1. Abre un issue en GitHub
2. Revisa la documentación de APIs
3. Consulta los logs de Docker

## 📄 Licencia

MIT License - Ver LICENSE.md

## 🙏 Agradecimientos

- Google Generative AI (Gemini)
- OpenAI (GPT-4o)
- ElevenLabs (TTS)
- Pexels (Stock de videos)
- MoviePy (Composición de video)
- Celery (Procesamiento asincrónico)
- FastAPI (Framework web)

---

**Hecho con ❤️ para creadores de contenido viral**
