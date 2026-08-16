"""
Ejemplos de uso del Generador de Clips Virales
===============================================

Este archivo contiene ejemplos prácticos para usar el sistema.
Descomenta y ejecuta según necesites.
"""

# ============================================================================
# EJEMPLO 1: Generar un guión simple
# ============================================================================

from 1_guiones import GuionGenerator
import json

try:
    generador = GuionGenerator()
    
    # Generar un guión para TikTok
    guion = generador.generar_guion(
        tema="3 hábitos para mejorar tu productividad",
        plataforma="tiktok",
        duracion=30,
        tono="viral"
    )
    
    if guion:
        print("\n=== GUIÓN GENERADO ===")
        print(json.dumps(guion, indent=2, ensure_ascii=False))
        
except Exception as e:
    print(f"Error: {e}")


# ============================================================================
# EJEMPLO 2: Generar audio desde un guión
# ============================================================================

"""
from 2_audio import AudioGenerator

audio_gen = AudioGenerator(lenguaje="es-ES", genero="femenino", velocidad=1.0)

# Usar el guión anterior para crear audio
if guion:
    texto = f"{guion['gancho']} {' '.join(guion['desarrollo'])} {guion['cierre']}"
    audio_gen.generar_audio(texto, "mi_primer_clip.mp3")
"""


# ============================================================================
# EJEMPLO 3: Generar múltiples variantes
# ============================================================================

"""
from 1_guiones import GuionGenerator

generador = GuionGenerator()

# Generar 3 variantes con diferentes tonos
variantes = generador.generar_multiples_variantes(
    tema="Recetas saludables fáciles",
    cantidad=3,
    plataforma="instagram"
)

print(f"Se generaron {len(variantes)} variantes")
"""


# ============================================================================
# EJEMPLO 4: Usar el generador completo
# ============================================================================

"""
from main import GeneradorClipsVirales

generador = GeneradorClipsVirales()

# Generar un clip viral completo (guión + audio)
clip = generador.generar_clip_completo(
    tema="Cómo meditar en 5 minutos",
    plataforma="youtube_shorts",
    duracion=45,
    tono="motivacional",
    generar_audio=True
)

if clip:
    print(f"Clip generado:")
    print(f"- Guión: {clip['ruta_guion']}")
    print(f"- Audio: {clip['ruta_audio']}")
"""


# ============================================================================
# EJEMPLO 5: Generar audio con diferentes voces
# ============================================================================

"""
from 2_audio import AudioGenerator

# Español de España - Mujer
audio_es = AudioGenerator(lenguaje="es-ES", genero="femenino")

# Español de México - Hombre
audio_mx = AudioGenerator(lenguaje="es-MX", genero="masculino")

# Español de Argentina - Mujer
audio_ar = AudioGenerator(lenguaje="es-AR", genero="femenino")

texto = "Hola, este es un ejemplo de síntesis de voz"

audio_es.generar_audio(texto, "audio_es_es.mp3")
audio_mx.generar_audio(texto, "audio_es_mx.mp3")
audio_ar.generar_audio(texto, "audio_es_ar.mp3")
"""


# ============================================================================
# EJEMPLO 6: Procesar temas desde un archivo
# ============================================================================

"""
import json
from main import GeneradorClipsVirales

# Supongamos que tienes un JSON con temas
temas = [
    {"titulo": "Productividad matinal", "plataforma": "tiktok"},
    {"titulo": "Recetas rápidas", "plataforma": "instagram"},
    {"titulo": "Tips de bienestar", "plataforma": "youtube_shorts"}
]

generador = GeneradorClipsVirales()

for tema_obj in temas:
    clip = generador.generar_clip_completo(
        tema=tema_obj["titulo"],
        plataforma=tema_obj["plataforma"],
        generar_audio=True
    )
    
    if clip:
        print(f"✓ {tema_obj['titulo']} - Completado")
"""


# ============================================================================
# EJEMPLO 7: Generar contenido en lote
# ============================================================================

"""
from 1_guiones import GuionGenerator
from 2_audio import AudioGenerator

generador_guion = GuionGenerator()
generador_audio = AudioGenerator()

# Lista de temas a generar
temas = [
    "5 formas de reducir estrés",
    "Cómo organizarse mejor en 10 pasos",
    "Ejercicios que puedes hacer en casa",
    "Alimentos que mejoran tu concentración",
    "Técnicas de relajación rápida"
]

for i, tema in enumerate(temas, 1):
    print(f"\nProcesando {i}/{len(temas)}: {tema}")
    
    # Generar guión
    guion = generador_guion.generar_guion(
        tema=tema,
        plataforma="tiktok",
        duracion=30
    )
    
    if guion:
        # Generar audio
        texto = f"{guion['gancho']} {' '.join(guion['desarrollo'])} {guion['cierre']}"
        nombre_archivo = f"audios/clip_{i:02d}.mp3"
        generador_audio.generar_audio(texto, nombre_archivo)
"""


# ============================================================================
# GUÍAS DE MEJORES PRÁCTICAS
# ============================================================================

"""
TIPS PARA MEJORES GUIONES:

1. ESPECIFICIDAD
   ✓ "Rutina matinal de 20 minutos para profesionales ocupados"
   ✗ "Rutina matinal"

2. TONOS RECOMENDADOS POR TIPO:
   - Educativo: "Cómo hacer X", "Tutorial de Y"
   - Viral: Consejos sorprendentes, "No lo sabías"
   - Motivacional: Historias inspiradoras, superación
   - Cómico: Situaciones relatable, humor

3. PLATAFORMAS Y DURACIÓN:
   - TikTok: 15-60 segundos, gancho en 3 primeros segundos
   - Instagram Reels: 15-90 segundos, énfasis visual
   - YouTube Shorts: 15-60 segundos, más sustancial

4. OPTIMIZACIÓN POR PLATAFORMA:
   TikTok: Velocidad, trending sounds, call-to-action claro
   Instagram: Estética visual, transiciones, influencers
   YouTube: Educación, autoridad, suscripción

5. VELOCIDAD DE AUDIO:
   0.8 - Más lento, énfasis en cada palabra
   1.0 - Velocidad normal, recomendado
   1.2 - Más rápido, energético
   1.5 - Muy rápido, contenido denso

6. PUNTUACIÓN EN GUIONES:
   - Usa signos de exclamación para entusiasmo
   - Pausas (...) donde el audio debe respirar
   - Preguntas retóricas para engagement
"""

print("Archivo de ejemplos cargado. Descomenta los ejemplos que necesites.")
