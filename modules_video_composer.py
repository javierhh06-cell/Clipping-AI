"""
Compositor de Video (Video Renderer)
El corazón computacional que orquesta la creación del video final
Usa moviepy + ffmpeg para máxima calidad y velocidad
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx, CompositeAudioClip
)
from moviepy.video.VideoClip import VideoClip
import numpy as np

logger = logging.getLogger(__name__)


class VideoComposer:
    """Compositor y renderizador de video"""
    
    SUPPORTED_CODECS = {
        "h264": {"codec": "libx264", "quality": "high"},
        "h265": {"codec": "libx265", "quality": "very_high"},
        "vp9": {"codec": "libvpx-vp9", "quality": "high"}
    }
    
    PRESET_CONFIGS = {
        "tiktok": {
            "resolution": (1080, 1920),  # 9:16
            "fps": 30,
            "bitrate": "8000k",
            "codec": "h264"
        },
        "instagram": {
            "resolution": (1080, 1350),  # Reels
            "fps": 30,
            "bitrate": "6000k",
            "codec": "h264"
        },
        "youtube_shorts": {
            "resolution": (1080, 1920),  # 9:16
            "fps": 60,
            "bitrate": "10000k",
            "codec": "h264"
        }
    }
    
    def __init__(self, platform: str = "tiktok", temp_dir: str = "/tmp/clips_virales"):
        """
        Inicializar el compositor
        
        Args:
            platform: Plataforma destino
            temp_dir: Directorio para archivos temporales
        """
        self.platform = platform
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.PRESET_CONFIGS.get(platform, self.PRESET_CONFIGS["tiktok"])
    
    async def compose_video(
        self,
        audio_path: str,
        broll_videos: List[Dict],
        subtitle_config: Dict,
        script_json: Dict,
        output_path: str,
        background_music: Optional[str] = None
    ) -> Optional[str]:
        """
        Componer el video final integrando todos los componentes
        
        Args:
            audio_path: Ruta del audio narrado
            broll_videos: Lista de videos B-Roll
            subtitle_config: Configuración de subtítulos dinámicos
            script_json: Guión en JSON
            output_path: Ruta de salida del video
            background_music: Ruta de música de fondo (opcional)
            
        Returns:
            Ruta del video generado o None si falló
        """
        
        try:
            logger.info(f"Iniciando composición de video para {self.platform}")
            
            # Paso 1: Construir video base con B-Roll
            logger.info("Paso 1: Construyendo video base con B-Roll")
            video_clips = await self._build_broll_sequence(broll_videos, script_json)
            
            if not video_clips:
                logger.error("No se pudieron crear clips de B-Roll")
                return None
            
            # Paso 2: Sincronizar audio y redimensionar video
            logger.info("Paso 2: Sincronizando audio")
            video_with_audio = await self._sync_audio(
                video_clips, audio_path, background_music
            )
            
            # Paso 3: Agregar subtítulos dinámicos
            logger.info("Paso 3: Agregando subtítulos dinámicos")
            video_with_subs = await self._add_dynamic_subtitles(
                video_with_audio, subtitle_config
            )
            
            # Paso 4: Renderizar video final
            logger.info("Paso 4: Renderizando video final")
            success = await self._render_video(video_with_subs, output_path)
            
            if success:
                logger.info(f"Video completado: {output_path}")
                return output_path
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error en composición de video: {e}")
            return None
    
    async def _build_broll_sequence(
        self,
        broll_videos: List[Dict],
        script_json: Dict
    ) -> Optional[List[VideoClip]]:
        """
        Construir secuencia de clips de B-Roll
        Cada sección del guión obtiene B-Roll correspondiente
        """
        
        clips = []
        
        try:
            # Organizar B-Roll por sección
            hook_videos = [v for v in broll_videos if v.get("section") == "hook"]
            body_videos = [v for v in broll_videos if v.get("section") == "body"]
            cta_videos = [v for v in broll_videos if v.get("section") == "cta"]
            
            # Hook
            if hook_videos:
                hook_duration = script_json.get("metadata", {}).get("total_duration", 30) * 0.1
                clip = await self._create_broll_clip(hook_videos[0], hook_duration)
                if clip:
                    clips.append(clip)
            
            # Body sections
            body_sections = script_json.get("body", [])
            body_duration_per_section = (
                script_json.get("metadata", {}).get("total_duration", 30) * 0.75 / len(body_sections)
            ) if body_sections else 0
            
            for i, section in enumerate(body_sections):
                if i < len(body_videos):
                    clip = await self._create_broll_clip(
                        body_videos[i], 
                        body_duration_per_section
                    )
                    if clip:
                        clips.append(clip)
            
            # CTA
            if cta_videos:
                cta_duration = script_json.get("metadata", {}).get("total_duration", 30) * 0.15
                clip = await self._create_broll_clip(cta_videos[0], cta_duration)
                if clip:
                    clips.append(clip)
            
            return clips if clips else None
        
        except Exception as e:
            logger.error(f"Error construyendo secuencia de B-Roll: {e}")
            return None
    
    async def _create_broll_clip(
        self,
        video_info: Dict,
        duration: float
    ) -> Optional[VideoClip]:
        """
        Crear clip de B-Roll redimensionado y procesado
        """
        
        try:
            url = video_info.get("url")
            if not url:
                return None
            
            logger.debug(f"Cargando video: {url}")
            clip = VideoFileClip(url)
            
            # Redimensionar a la resolución de la plataforma
            target_width, target_height = self.config["resolution"]
            clip = clip.resize(height=target_height)
            
            # Crop si es necesario
            if clip.w > target_width:
                x_center = clip.w / 2
                clip = clip.crop(
                    x1=int(x_center - target_width / 2),
                    x2=int(x_center + target_width / 2)
                )
            
            # Ajustar duración
            if clip.duration > duration:
                clip = clip.subclipped(0, duration)
            elif clip.duration < duration:
                # Loop si es más corto
                num_loops = int(duration / clip.duration) + 1
                clips = [clip.copy() for _ in range(num_loops)]
                clip = concatenate_videoclips(clips).subclipped(0, duration)
            
            # Agregar transición de fade
            clip = clip.fx(vfx.fadein, duration=0.3).fx(vfx.fadeout, duration=0.3)
            
            return clip
        
        except Exception as e:
            logger.error(f"Error creando clip de B-Roll: {e}")
            return None
    
    async def _sync_audio(
        self,
        video_clips: List[VideoClip],
        audio_path: str,
        background_music: Optional[str] = None
    ) -> Optional[VideoClip]:
        """
        Sincronizar audio con video
        Mezclar voz narrada con música de fondo (opcional)
        """
        
        try:
            # Concatenar clips de video
            logger.debug("Concatenando clips de video")
            if len(video_clips) == 1:
                video = video_clips[0]
            else:
                video = concatenate_videoclips(video_clips)
            
            # Redimensionar video a resolución exacta si es necesario
            target_width, target_height = self.config["resolution"]
            if (video.w, video.h) != (target_width, target_height):
                video = video.resize((target_width, target_height))
            
            # Cargar audio narrado
            logger.debug(f"Cargando audio: {audio_path}")
            narration_audio = AudioFileClip(audio_path)
            
            # Asegurar que el video dure lo que el audio
            video = video.set_duration(narration_audio.duration)
            
            # Crear mezcla de audio
            if background_music:
                logger.debug(f"Cargando música de fondo: {background_music}")
                bg_audio = AudioFileClip(background_music)
                
                # Ajustar duración de música de fondo
                if bg_audio.duration < narration_audio.duration:
                    # Loop música de fondo
                    num_loops = int(narration_audio.duration / bg_audio.duration) + 1
                    bg_clips = [bg_audio.copy() for _ in range(num_loops)]
                    bg_audio = concatenate_videoclips(bg_clips)
                
                bg_audio = bg_audio.set_duration(narration_audio.duration)
                
                # Mezclar: 70% narración, 30% música de fondo
                final_audio = CompositeAudioClip([
                    narration_audio.volumex(0.7),
                    bg_audio.volumex(0.3)
                ])
            else:
                final_audio = narration_audio
            
            # Establecer audio en video
            video_with_audio = video.set_audio(final_audio)
            
            # Configurar FPS
            video_with_audio = video_with_audio.set_fps(self.config["fps"])
            
            return video_with_audio
        
        except Exception as e:
            logger.error(f"Error sincronizando audio: {e}")
            return None
    
    async def _add_dynamic_subtitles(
        self,
        video: VideoClip,
        subtitle_config: Dict
    ) -> Optional[VideoClip]:
        """
        Agregar subtítulos dinámicos con animaciones
        """
        
        try:
            subtitle_clips = []
            style = subtitle_config.get("style", {})
            frames = subtitle_config.get("frames", [])
            
            if not frames:
                logger.warning("No hay frames de subtítulos para procesar")
                return video
            
            logger.debug(f"Procesando {len(frames)} frames de subtítulos")
            
            for frame in frames:
                start_time = frame["start_ms"] / 1000.0
                end_time = frame["end_ms"] / 1000.0
                text = frame["text"]
                
                # Crear clip de texto
                txt_clip = TextClip(
                    txt=text,
                    fontsize=style.get("font_size", 48),
                    font=style.get("font_family", "Arial"),
                    color=frame.get("color_override", style.get("primary_color", "white")),
                    method='caption',
                    size=(
                        self.config["resolution"][0] - 100,
                        None
                    ),
                    stroke_width=2,
                    stroke_color=style.get("shadow_color", "black")
                )
                
                # Aplicar animación
                animation = frame.get("animation", "fade")
                if animation == "pop":
                    txt_clip = txt_clip.set_duration(end_time - start_time)
                    txt_clip = txt_clip.fx(vfx.resize, lambda t: 1 + 0.1 * np.sin(t * 20))
                else:
                    txt_clip = txt_clip.fx(vfx.fadein, 0.1).fx(vfx.fadeout, 0.1)
                    txt_clip = txt_clip.set_duration(end_time - start_time)
                
                # Posicionar en pantalla
                txt_clip = txt_clip.set_position(("center", "bottom"))
                txt_clip = txt_clip.set_start(start_time)
                
                subtitle_clips.append(txt_clip)
            
            # Componer video con subtítulos
            final_video = CompositeVideoClip(
                [video] + subtitle_clips,
                size=self.config["resolution"]
            )
            
            return final_video
        
        except Exception as e:
            logger.error(f"Error agregando subtítulos: {e}")
            return video  # Retornar video sin subtítulos si falla
    
    async def _render_video(
        self,
        video: VideoClip,
        output_path: str
    ) -> bool:
        """
        Renderizar el video final a archivo
        """
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Renderizando video a: {output_path}")
            
            codec_config = self.SUPPORTED_CODECS[self.config.get("codec", "h264")]
            
            video.write_videofile(
                output_path,
                fps=self.config["fps"],
                codec=codec_config["codec"],
                audio_codec="aac",
                bitrate=self.config.get("bitrate", "8000k"),
                preset="fast",  # veryfast, fast, medium, slow
                verbose=False,
                logger=None,
                threads=4
            )
            
            logger.info(f"Renderizado completado exitosamente")
            return True
        
        except Exception as e:
            logger.error(f"Error renderizando video: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Limpiar archivos temporales"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            logger.info("Archivos temporales eliminados")
        except Exception as e:
            logger.error(f"Error limpiando archivos temporales: {e}")


def get_video_composer(platform: str = "tiktok") -> VideoComposer:
    """Factory para obtener compositor de video"""
    return VideoComposer(platform=platform)
