"""
Módulo de Síntesis de Voz (TTS)
Soporta ElevenLabs API y Coqui (local)
"""

import asyncio
import aiohttp
from typing import Optional
from pathlib import Path
import logging
from config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """Motor de síntesis de voz"""
    
    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
    
    # Voces premium de ElevenLabs (IDs)
    VOICES = {
        "es-ES": {
            "femenino": "EXAVITQu4yMkVMd7gJ7b",  # Premios pro voice
            "masculino": "MF3mGyEYCl7XYWbV9V6O"
        },
        "es-MX": {
            "femenino": "Z28Pc6JHmPvSMf3S8Mao",
            "masculino": "9gCvMjr9LuL9xN6pL8xK"
        },
        "es-AR": {
            "femenino": "DJWFqZHaJvJUxxJQhV6S",
            "masculino": "l2pZJ7p5t2iMqKH5lK8x"
        }
    }
    
    def __init__(self, provider: str = "elevenlabs"):
        """
        Inicializar el motor TTS
        
        Args:
            provider: "elevenlabs" o "coqui"
        """
        self.provider = provider
        self.session = None
        
        if provider == "elevenlabs":
            if not settings.elevenlabs_api_key:
                raise ValueError("ELEVENLABS_API_KEY no configurada")
            self.api_key = settings.elevenlabs_api_key
        elif provider == "coqui":
            # Coqui no requiere API key, se usa localmente
            try:
                import torch
                import torchaudio
                from TTS.api import TTS
                self.tts_model = TTS(model_name="tts_models/es/mai/glow-tts")
                logger.info("Modelo Coqui cargado exitosamente")
            except ImportError:
                logger.error("TTS (Coqui) no instalado. Ejecuta: pip install tts")
                raise
        else:
            raise ValueError(f"Provider no soportado: {provider}")
    
    async def synthesize(
        self,
        text: str,
        language: str = "es-ES",
        gender: str = "femenino",
        speed: float = 1.0,
        output_path: str = "output.mp3"
    ) -> bool:
        """
        Sintetizar texto a voz
        
        Args:
            text: Texto a sintetizar
            language: Código de lenguaje
            gender: Género de la voz
            speed: Velocidad de reproducción (0.5 - 2.0)
            output_path: Ruta de salida del MP3
            
        Returns:
            True si fue exitoso
        """
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if self.provider == "elevenlabs":
                return await self._synthesize_elevenlabs(
                    text, language, gender, speed, output_path
                )
            else:
                return await self._synthesize_coqui(
                    text, language, gender, speed, output_path
                )
        
        except Exception as e:
            logger.error(f"Error sintetizando voz: {e}")
            return False
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        language: str,
        gender: str,
        speed: float,
        output_path: str
    ) -> bool:
        """Sintetizar usando ElevenLabs API"""
        
        # Obtener ID de voz
        voice_id = self.VOICES.get(language, {}).get(gender)
        if not voice_id:
            logger.warning(f"Voz no disponible: {language}/{gender}. Usando predeterminada.")
            voice_id = self.VOICES["es-ES"]["femenino"]
        
        url = f"{self.ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Modelo con mejor calidad
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    logger.info(f"Audio guardado en: {output_path}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Error ElevenLabs: {response.status} - {error}")
                    return False
        except Exception as e:
            logger.error(f"Error en request ElevenLabs: {e}")
            return False
    
    async def _synthesize_coqui(
        self,
        text: str,
        language: str,
        gender: str,
        speed: float,
        output_path: str
    ) -> bool:
        """Sintetizar usando Coqui TTS (local)"""
        
        def tts_sync():
            self.tts_model.tts_to_file(
                text=text,
                file_path=output_path,
                speed=speed
            )
        
        # Ejecutar en thread para no bloquear el loop async
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, tts_sync)
            logger.info(f"Audio Coqui guardado en: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error Coqui TTS: {e}")
            return False
    
    async def synthesize_with_timestamps(
        self,
        text: str,
        language: str = "es-ES",
        gender: str = "femenino",
        output_path: str = "output.mp3"
    ) -> Optional[dict]:
        """
        Sintetizar y obtener timestamps de palabras para subtítulos
        
        Returns:
            {
                "audio_path": str,
                "duration_ms": int,
                "word_timestamps": [
                    {"word": str, "start_ms": int, "end_ms": int}
                ]
            }
        """
        
        if not await self.synthesize(text, language, gender, output_path=output_path):
            return None
        
        # Obtener duración del audio
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(output_path)
            duration_ms = len(audio)
        except Exception as e:
            logger.error(f"Error obteniendo duración de audio: {e}")
            duration_ms = len(text) * 100  # Aproximación
        
        # Usar Whisper para obtener timestamps de palabras
        try:
            import whisper
            result = whisper.transcribe(output_path, language="es")
            
            word_timestamps = []
            for segment in result["segments"]:
                for word_info in segment.get("words", []):
                    word_timestamps.append({
                        "word": word_info["word"],
                        "start_ms": int(word_info["start"] * 1000),
                        "end_ms": int(word_info["end"] * 1000)
                    })
            
            return {
                "audio_path": output_path,
                "duration_ms": duration_ms,
                "word_timestamps": word_timestamps,
                "text": text
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo timestamps: {e}")
            return {
                "audio_path": output_path,
                "duration_ms": duration_ms,
                "word_timestamps": [],
                "text": text
            }
    
    async def close(self):
        """Cerrar sesión HTTP"""
        if self.session:
            await self.session.close()
    
    def __del__(self):
        """Cleanup al destruir objeto"""
        if self.session:
            try:
                asyncio.run(self.close())
            except:
                pass


def get_tts_engine(provider: str = "elevenlabs") -> TTSEngine:
    """Factory para obtener motor TTS"""
    return TTSEngine(provider=provider)
