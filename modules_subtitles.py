"""
Módulo de Subtítulos Dinámicos Sincronizados
Usa OpenAI Whisper para extraer timestamps de palabras
"""

import whisper
import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Generador de subtítulos sincronizados"""
    
    def __init__(self, model_name: str = "base"):
        """
        Inicializar generador de subtítulos
        
        Args:
            model_name: Modelo de Whisper a usar (tiny, base, small, medium, large)
        """
        logger.info(f"Cargando modelo Whisper: {model_name}")
        self.model = whisper.load_model(model_name)
    
    async def generate_subtitle_timestamps(
        self,
        audio_path: str,
        language: str = "es"
    ) -> Optional[Dict]:
        """
        Generar timestamps de palabras desde audio
        
        Args:
            audio_path: Ruta del archivo de audio MP3
            language: Código de lenguaje
            
        Returns:
            {
                "duration_ms": int,
                "word_timestamps": [
                    {"word": str, "start_ms": int, "end_ms": int, "confidence": float}
                ],
                "segment_timestamps": [
                    {"text": str, "start_ms": int, "end_ms": int}
                ]
            }
        """
        
        try:
            # Transcribir con Whisper
            logger.info(f"Transcribiendo audio: {audio_path}")
            result = self.model.transcribe(audio_path, language=language, word_level_timestamps=True)
            
            word_timestamps = []
            segment_timestamps = []
            
            duration_ms = 0
            
            # Procesar segmentos
            for segment in result["segments"]:
                segment_start_ms = int(segment["start"] * 1000)
                segment_end_ms = int(segment["end"] * 1000)
                duration_ms = max(duration_ms, segment_end_ms)
                
                segment_timestamps.append({
                    "text": segment["text"],
                    "start_ms": segment_start_ms,
                    "end_ms": segment_end_ms,
                    "confidence": segment.get("confidence", 1.0)
                })
                
                # Extraer timestamps de palabras si están disponibles
                if "words" in segment:
                    for word_info in segment["words"]:
                        word_timestamps.append({
                            "word": word_info["word"].strip(),
                            "start_ms": int(word_info["start"] * 1000),
                            "end_ms": int(word_info["end"] * 1000),
                            "confidence": word_info.get("confidence", 1.0)
                        })
                else:
                    # Fallback: aproximar timestamps de palabras
                    words = segment["text"].split()
                    segment_duration = segment_end_ms - segment_start_ms
                    word_duration = segment_duration / len(words) if words else 0
                    
                    for i, word in enumerate(words):
                        word_timestamps.append({
                            "word": word,
                            "start_ms": int(segment_start_ms + i * word_duration),
                            "end_ms": int(segment_start_ms + (i + 1) * word_duration),
                            "confidence": 0.5  # Confianza baja para timestamps aproximados
                        })
            
            return {
                "duration_ms": duration_ms,
                "word_timestamps": word_timestamps,
                "segment_timestamps": segment_timestamps,
                "full_text": result["text"],
                "language": language
            }
        
        except Exception as e:
            logger.error(f"Error generando subtítulos: {e}")
            return None
    
    def format_subtitles_srt(
        self,
        timestamps: Dict
    ) -> str:
        """
        Formatear subtítulos en formato SRT
        
        Args:
            timestamps: Dict retornado por generate_subtitle_timestamps
            
        Returns:
            String en formato SRT
        """
        
        srt_content = ""
        
        for i, segment in enumerate(timestamps["segment_timestamps"], 1):
            start_time = self._ms_to_srt_time(segment["start_ms"])
            end_time = self._ms_to_srt_time(segment["end_ms"])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{segment['text']}\n"
            srt_content += "\n"
        
        return srt_content
    
    def format_subtitles_vtt(
        self,
        timestamps: Dict
    ) -> str:
        """Formatear subtítulos en formato WebVTT"""
        
        vtt_content = "WEBVTT\n\n"
        
        for segment in timestamps["segment_timestamps"]:
            start_time = self._ms_to_vtt_time(segment["start_ms"])
            end_time = self._ms_to_vtt_time(segment["end_ms"])
            
            vtt_content += f"{start_time} --> {end_time}\n"
            vtt_content += f"{segment['text']}\n"
            vtt_content += "\n"
        
        return vtt_content
    
    def generate_dynamic_subtitle_config(
        self,
        timestamps: Dict,
        style_config: Optional[Dict] = None
    ) -> Dict:
        """
        Generar configuración para renderizar subtítulos dinámicos
        Optimizado para viralidad: destacar palabras clave, colores, efectos
        
        Args:
            timestamps: Dict de timestamps
            style_config: Configuración de estilos (fuentes, colores, etc.)
            
        Returns:
            Configuración para compositor de video
        """
        
        if not style_config:
            style_config = {
                "font_family": "Arial",
                "font_size": 48,
                "primary_color": "#FFFFFF",
                "highlight_color": "#FF1493",  # Rosa vibrante para keywords
                "shadow_color": "#000000",
                "shadow_offset": (2, 2),
                "background_color": "rgba(0, 0, 0, 0.3)",
                "background_padding": 10,
                "position": "bottom_center",
                "animation": "fade_pop"  # fade, pop, slide, bounce
            }
        
        subtitle_config = {
            "style": style_config,
            "frames": []
        }
        
        # Generar frames de subtítulos
        for word in timestamps["word_timestamps"]:
            frame_config = {
                "start_ms": word["start_ms"],
                "end_ms": word["end_ms"],
                "text": word["word"],
                "is_keyword": self._is_keyword(word["word"]),
                "animation": "pop" if self._is_keyword(word["word"]) else "fade"
            }
            
            if self._is_keyword(word["word"]):
                frame_config["color_override"] = style_config["highlight_color"]
                frame_config["scale"] = 1.2
                frame_config["effect"] = "shake"
            
            subtitle_config["frames"].append(frame_config)
        
        return subtitle_config
    
    def _is_keyword(self, word: str) -> bool:
        """Detectar si una palabra es keyword para resaltar"""
        
        keywords = {
            "increíble", "sorprendente", "viral", "espectacular",
            "mejor", "único", "nunca", "ahora", "click", "aquí",
            "suscríbete", "sígueme", "comparte", "gratis", "rápido"
        }
        
        return word.lower().strip(",.!?;:") in keywords
    
    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """Convertir milisegundos a formato SRT: HH:MM:SS,mmm"""
        seconds = ms // 1000
        milliseconds = ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    @staticmethod
    def _ms_to_vtt_time(ms: int) -> str:
        """Convertir milisegundos a formato WebVTT: HH:MM:SS.mmm"""
        seconds = ms // 1000
        milliseconds = ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def save_subtitle_file(
        self,
        timestamps: Dict,
        output_path: str,
        format_type: str = "srt"
    ) -> bool:
        """
        Guardar subtítulos a archivo
        
        Args:
            timestamps: Dict de timestamps
            output_path: Ruta de salida
            format_type: "srt" o "vtt"
            
        Returns:
            True si fue exitoso
        """
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "srt":
                content = self.format_subtitles_srt(timestamps)
            elif format_type == "vtt":
                content = self.format_subtitles_vtt(timestamps)
            else:
                raise ValueError(f"Formato no soportado: {format_type}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Subtítulos guardados en: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error guardando subtítulos: {e}")
            return False
    
    def save_dynamic_subtitle_config(
        self,
        config: Dict,
        output_path: str
    ) -> bool:
        """Guardar configuración de subtítulos dinámicos en JSON"""
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuración de subtítulos guardada en: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error guardando configuración de subtítulos: {e}")
            return False


def get_subtitle_generator(model: str = "base") -> SubtitleGenerator:
    """Factory para obtener generador de subtítulos"""
    return SubtitleGenerator(model_name=model)
