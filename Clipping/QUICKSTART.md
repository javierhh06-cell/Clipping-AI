"""
GUÍA RÁPIDA DE INICIO
=====================

Este archivo contiene todos los comandos necesarios para poner en marcha
el sistema Generador de Clips Virales.
"""

# ============================================================================
# 1. INSTALACIÓN RÁPIDA CON DOCKER
# ============================================================================

# Si tienes Docker instalado, es la forma más fácil:
docker-compose up -d

# Verificar que todo está corriendo:
docker ps
curl http://localhost:8000/health

# Dashboard de Celery (Flower):
# Accede a http://localhost:5555


# ============================================================================
# 2. INSTALACIÓN LOCAL (Sin Docker)
# ============================================================================

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar y editar .env
cp .env.example .env
# Editar .env con tus claves API

# Iniciar Redis (en otra terminal)
redis-server
# o con Docker: docker run -d -p 6379:6379 redis:7

# Iniciar PostgreSQL (en otra terminal)
# O con Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Inicializar base de datos
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Iniciar Celery Worker (terminal 1)
celery -A celery_config worker -l info

# Iniciar FastAPI (terminal 2)
uvicorn app:app --reload --port 8000

# Verificar en terminal 3
curl http://localhost:8000/health


# ============================================================================
# 3. CONFIGURAR VARIABLES DE ENTORNO (.env)
# ============================================================================

# Copiar plantilla
cp .env.example .env

# Editar con tus credenciales:
nano .env

# Variables requeridas MÍNIMAS:
# - DATABASE_URL (PostgreSQL)
# - REDIS_URL
# - GOOGLE_API_KEY o OPENAI_API_KEY
# - ELEVENLABS_API_KEY
# - PEXELS_API_KEY
# - AWS o GCS (para almacenamiento)
# - OAuth2 keys (YouTube, Instagram, TikTok)


# ============================================================================
# 4. PRIMEROS PASOS - HACER UN REQUEST
# ============================================================================

# Request básico de generación de video
curl -X POST "http://localhost:8000/api/v1/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "5 consejos de productividad para profesionales",
    "platform": "tiktok",
    "tone": "viral",
    "duration": 30
  }'

# Respuesta esperada:
{
  "status": "queued",
  "project_id": 1,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Video en cola para procesamiento",
  "track_url": "/api/v1/videos/1/progress"
}

# Monitorear progreso
curl "http://localhost:8000/api/v1/videos/1/progress"

# Obtener video cuando esté listo
curl "http://localhost:8000/api/v1/videos/1"


# ============================================================================
# 5. USAR EN PYTHON
# ============================================================================

# Script Python para generar video programáticamente
python << 'EOF'
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# Generar video
response = requests.post(f"{BASE_URL}/api/v1/videos/generate", json={
    "topic": "Cómo meditar en 5 minutos",
    "platform": "youtube_shorts",
    "tone": "motivacional",
    "duration": 45
})

data = response.json()
project_id = data["project_id"]
job_id = data["job_id"]

print(f"Proyecto {project_id} creado. Job: {job_id}")

# Monitorear progreso
for i in range(60):  # Máximo 60 intentos (5 minutos)
    progress = requests.get(f"{BASE_URL}/api/v1/videos/{project_id}/progress").json()
    
    print(f"Progreso: {progress['progress']}% - Paso: {progress.get('current_step', 'N/A')}")
    
    if progress['status'] == 'SUCCESS':
        print(f"✓ Video completado!")
        video = requests.get(f"{BASE_URL}/api/v1/videos/{project_id}").json()
        print(json.dumps(video, indent=2, default=str))
        break
    
    elif progress['status'] == 'FAILURE':
        print("✗ Error en la generación")
        break
    
    time.sleep(5)  # Esperar 5 segundos entre intentos

EOF


# ============================================================================
# 6. DOCKER - COMANDOS ÚTILES
# ============================================================================

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api                    # Logs de la API
docker-compose logs -f celery_worker          # Logs del worker
docker-compose logs -f db                     # Logs de BD
docker-compose logs -f redis                  # Logs de Redis

# Parar servicios
docker-compose down

# Reiniciar un servicio específico
docker-compose restart api
docker-compose restart celery_worker

# Acceder a base de datos
docker-compose exec db psql -U clips_user -d clips_virales_db

# Acceder a Redis
docker-compose exec redis redis-cli

# Ver recursos usados
docker stats


# ============================================================================
# 7. CELERY - MONITOREO
# ============================================================================

# Ver tareas en cola
celery -A celery_config inspect active

# Ver workers activos
celery -A celery_config inspect active_queues

# Purgar cola (¡CUIDADO! Elimina todos los jobs)
celery -A celery_config purge

# Iniciar Flower (dashboard web)
celery -A celery_config flower --port=5555
# Acceder a http://localhost:5555


# ============================================================================
# 8. BASE DE DATOS - UTILIDADES
# ============================================================================

# Resetear base de datos (¡CUIDADO! Elimina todos los datos)
python << 'EOF'
from database import Base, engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Base de datos reseteada")
EOF

# Hacer backup
pg_dump -U clips_user -h localhost -d clips_virales_db > backup.sql

# Restaurar desde backup
psql -U clips_user -h localhost -d clips_virales_db < backup.sql


# ============================================================================
# 9. DEBUGGING Y TROUBLESHOOTING
# ============================================================================

# Verificar conexión a APIs
python << 'EOF'
from config import settings
from modules_script_generator import get_script_generator
from modules_tts import get_tts_engine

# Test Gemini
try:
    gen = get_script_generator("gemini")
    print("✓ Gemini API conectado")
except Exception as e:
    print(f"✗ Error en Gemini: {e}")

# Test TTS
try:
    tts = get_tts_engine()
    print("✓ TTS Engine inicializado")
except Exception as e:
    print(f"✗ Error en TTS: {e}")

print("✓ Todas las conexiones OK")
EOF

# Verificar FFmpeg
ffmpeg -version
ffprobe -version

# Verificar PostgreSQL
psql --version
# Conectar: psql postgresql://clips_user:clips_password@localhost:5432/clips_virales_db

# Verificar Redis
redis-cli ping
# Debe responder: PONG


# ============================================================================
# 10. DEPLOYMENT EN PRODUCCIÓN
# ============================================================================

# Compilar imagen Docker
docker build -t clips-api:latest .
docker build -f Dockerfile.celery -t clips-celery:latest .

# Push a registry
docker tag clips-api:latest your-registry/clips-api:latest
docker push your-registry/clips-api:latest

# En producción con SSL/TLS:
# Usar Nginx como reverse proxy
# Configurar Let's Encrypt para certificados SSL
# Usar variables de entorno seguras (AWS Secrets Manager, etc.)
# Habilitar CORS restringido
# Implementar rate limiting
# Agregar logging centralizado (CloudWatch, DataDog, etc.)


# ============================================================================
# 11. PRUEBAS
# ============================================================================

# Ejecutar tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=. --cov-report=html

# Linting
black . --check
flake8 .
mypy . --ignore-missing-imports


# ============================================================================
# 12. PERFORMANCE Y TUNING
# ============================================================================

# Aumentar workers de Celery
celery -A celery_config worker -l info --concurrency=8

# Usar diferentes pools
celery -A celery_config worker -l info --pool=prefork --concurrency=4
celery -A celery_config worker -l info --pool=gevent --concurrency=1000

# Monitorear performance
pip install py-spy
py-spy record -o profile.svg -- celery -A celery_config worker

# Profiling de API
pip install pyflame
pyflame -s 60 -r 100 -o flames.svg --pid <PID>


# ============================================================================
# 13. ACTUALIZAR DEPENDENCIAS
# ============================================================================

# Ver qué necesita actualización
pip list --outdated

# Actualizar todo
pip install --upgrade -r requirements.txt

# Actualizar un paquete específico
pip install --upgrade fastapi


# ============================================================================
# 14. BACKUP Y RECUPERACIÓN
# ============================================================================

# Backup de base de datos
docker-compose exec db pg_dump -U clips_user -d clips_virales_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup de videos en S3
aws s3 sync s3://clips-virales-prod/videos ./backups/videos/

# Restaurar desde backup
docker-compose exec -T db psql -U clips_user -d clips_virales_db < backup.sql


# ============================================================================
# 15. RECURSOS ÚTILES
# ============================================================================

# FastAPI Documentation: https://fastapi.tiangolo.com
# Celery: https://docs.celeryproject.io
# SQLAlchemy: https://docs.sqlalchemy.org
# Docker: https://docs.docker.com
# PostgreSQL: https://www.postgresql.org/docs/
# MoviePy: https://zulko.github.io/moviepy/
# Pydantic: https://docs.pydantic.dev

echo "Guía rápida completada. ¡Listo para comenzar!"
