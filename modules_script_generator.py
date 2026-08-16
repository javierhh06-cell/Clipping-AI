"""
Módulo de Generación de Guiones con LLMs
Soporta GPT-4o (OpenAI) y Gemini 1.5 Pro (Google)
"""

import json
from typing import Dict, List, Optional
import google.generativeai as genai
from openai import AsyncOpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generador de guiones para clips virales usando LLMs"""
    
    # System prompt estructurado para garantizar JSON válido
    SYSTEM_PROMPT = """Eres un experto en crear guiones para clips virales optimizados para redes sociales.

Tu tarea es generar guiones en formato JSON estrictamente estructurado.

IMPORTANTE: Siempre devuelve SOLO JSON válido, sin explicaciones adicionales.

Estructura JSON requerida:
{
    "hook": {
        "text": "Frase de gancho (máximo 10 palabras para captar atención en 3 segundos)",
        "visual_cue": "Descripción breve del visual que acompaña"
    },
    "body": [
        {
            "narration": "Texto a narrar (máximo 20 palabras por sección)",
            "visual_description": "Descripción detallada del visual correspondiente",
            "duration_seconds": 5,
            "broll_keywords": ["keyword1", "keyword2"],
            "visual_effects": ["transición sugerida", "efecto visual"]
        }
    ],
    "cta": {
        "text": "Call-to-action claro (seguir, comentar, suscribirse, etc.)",
        "visual_cue": "Visual de cierre"
    },
    "metadata": {
        "total_duration": 30,
        "platform": "tiktok",
        "tone": "viral",
        "target_audience": "Young professionals",
        "key_keywords": ["keyword1", "keyword2"],
        "hashtags": ["#hashtag1", "#hashtag2"],
        "music_suggestions": ["upbeat electronic", "motivational"]
    },
    "production_tips": [
        "Tip 1",
        "Tip 2",
        "Tip 3"
    ]
}

Reglas:
- Ganchos impactantes que capturen atención en 3 segundos
- Lenguaje natural y conversacional
- Incluye sorpresa, valor o humor
- Optimiza para máximo engagement
- Descripciones visuales detalladas para el compositor de video
- B-Roll keywords específicos para búsquedas
"""
    
    PLATFORM_SETTINGS = {
        "tiktok": {
            "max_duration": 60,
            "hook_critical": True,
            "pacing": "fast",
            "text_overlay": True,
            "sound_design": "trending"
        },
        "instagram": {
            "max_duration": 90,
            "hook_critical": True,
            "pacing": "moderate",
            "text_overlay": True,
            "aspect_ratio": "9:16",
            "sound_design": "upbeat"
        },
        "youtube_shorts": {
            "max_duration": 60,
            "hook_critical": False,
            "pacing": "moderate",
            "text_overlay": False,
            "sound_design": "professional"
        }
    }
    
    def __init__(self, provider: str = "gemini"):
        """
        Inicializar el generador
        
        Args:
            provider: "gemini" o "openai"
        """
        self.provider = provider
        
        if provider == "gemini":
            genai.configure(api_key=settings.google_api_key)
            self.model_gemini = genai.GenerativeModel('gemini-1.5-pro')
        elif provider == "openai":
            self.client_openai = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Provider no soportado: {provider}")
    
    async def generate_script(
        self,
        topic: str,
        platform: str = "tiktok",
        duration: int = 30,
        tone: str = "viral",
        additional_context: Optional[str] = None
    ) -> Dict:
        """
        Generar un guión estructurado en JSON
        
        Args:
            topic: Tema del clip
            platform: Plataforma destino
            duration: Duración deseada en segundos
            tone: Tono del guión
            additional_context: Contexto adicional para el guión
            
        Returns:
            Diccionario con el guión estructurado
        """
        
        platform_config = self.PLATFORM_SETTINGS.get(platform, self.PLATFORM_SETTINGS["tiktok"])
        
        user_prompt = f"""Genera un guión viral para {platform}.

TEMA: {topic}
DURACIÓN: {duration} segundos
TONO: {tone}
PLATAFORMA: {platform}

Configuración de plataforma:
- Hook crítico: {platform_config['hook_critical']}
- Ritmo: {platform_config['pacing']}
- Overlay de texto: {platform_config['text_overlay']}

{f'Contexto adicional: {additional_context}' if additional_context else ''}

Genera el guión en JSON válido siguiendo la estructura exacta especificada."""
        
        try:
            if self.provider == "gemini":
                script = await self._generate_with_gemini(user_prompt)
            else:
                script = await self._generate_with_openai(user_prompt)
            
            # Validar JSON
            if isinstance(script, str):
                script = json.loads(script)
            
            # Agregar metadata
            script["metadata"]["platform"] = platform
            script["metadata"]["tone"] = tone
            script["metadata"]["total_duration"] = duration
            
            logger.info(f"Script generado exitosamente para: {topic}")
            return script
            
        except Exception as e:
            logger.error(f"Error generando script: {e}")
            raise
    
    async def _generate_with_gemini(self, user_prompt: str) -> Dict:
        """Generar guión usando Google Gemini"""
        
        response = self.model_gemini.generate_content(
            [self.SYSTEM_PROMPT, user_prompt],
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048
            )
        )
        
        # Extraer JSON de la respuesta
        text = response.text
        
        # Si el modelo incluye markdown, extraerlo
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text
        
        return json.loads(json_str)
    
    async def _generate_with_openai(self, user_prompt: str) -> Dict:
        """Generar guión usando OpenAI GPT-4o"""
        
        response = await self.client_openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_variants(
        self,
        topic: str,
        platform: str = "tiktok",
        quantity: int = 3
    ) -> List[Dict]:
        """
        Generar múltiples variantes de un guión
        
        Args:
            topic: Tema base
            platform: Plataforma
            quantity: Número de variantes
            
        Returns:
            Lista de scripts
        """
        
        tones = ["viral", "educativo", "cómico"][:quantity]
        scripts = []
        
        for tone in tones:
            logger.info(f"Generando variante: {tone}")
            script = await self.generate_script(
                topic=topic,
                platform=platform,
                tone=tone
            )
            scripts.append(script)
        
        return scripts


# Instancia global
def get_script_generator(provider: str = "gemini") -> ScriptGenerator:
    """Factory para obtener generador de scripts"""
    return ScriptGenerator(provider=provider)
