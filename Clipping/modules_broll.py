"""
Módulo de Recolección de B-Roll y Multimedia
Integra Pexels API y repositorio de videos personalizados
"""

import aiohttp
import logging
from typing import List, Dict, Optional
from config import settings
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class BRollManager:
    """Gestor de B-Roll y multimedia"""
    
    PEXELS_API_URL = "https://api.pexels.com/v1"
    
    # Categorías y palabras clave para búsquedas optimizadas
    BROLL_CATEGORIES = {
        "viral": ["trending", "satisfying", "aesthetic", "smooth"],
        "educational": ["explanation", "tutorial", "professional", "corporate"],
        "comedy": ["funny", "relatable", "meme", "reaction"],
        "motivational": ["inspiration", "success", "achievement", "growth"]
    }
    
    # Repositorio interno de loops de video
    INTERNAL_LOOPS = {
        "parkour_gta5": {
            "url": "gs://bucket/loops/parkour_gta5.mp4",
            "duration": 5,
            "tags": ["parkour", "action", "urban"]
        },
        "minecraft_jumps": {
            "url": "gs://bucket/loops/minecraft_jumps.mp4",
            "duration": 3,
            "tags": ["minecraft", "gaming", "action"]
        },
        "satisfying": {
            "url": "gs://bucket/loops/satisfying.mp4",
            "duration": 4,
            "tags": ["satisfying", "asmr", "oddly satisfying"]
        },
        "coding": {
            "url": "gs://bucket/loops/coding.mp4",
            "duration": 5,
            "tags": ["coding", "tech", "programming"]
        },
        "nature": {
            "url": "gs://bucket/loops/nature.mp4",
            "duration": 6,
            "tags": ["nature", "landscape", "calming"]
        }
    }
    
    def __init__(self):
        """Inicializar el gestor de B-Roll"""
        if not settings.pexels_api_key:
            logger.warning("PEXELS_API_KEY no configurada. Solo usará repositorio interno.")
        self.session = None
    
    async def search_broll(
        self,
        keywords: List[str],
        duration_seconds: int = 30,
        quantity: int = 5,
        orientation: str = "portrait"  # "portrait" para redes sociales
    ) -> List[Dict]:
        """
        Buscar B-Roll en Pexels
        
        Args:
            keywords: Lista de palabras clave para buscar
            duration_seconds: Duración deseada
            quantity: Cantidad de videos a retornar
            orientation: Orientación del video
            
        Returns:
            Lista de videos encontrados
        """
        
        results = []
        
        for keyword in keywords:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                # Primero buscar en repositorio interno
                internal = await self._search_internal(keyword)
                results.extend(internal[:quantity // len(keywords)])
                
                # Luego buscar en Pexels si está disponible
                if settings.pexels_api_key:
                    pexels = await self._search_pexels(keyword, quantity)
                    results.extend(pexels[:quantity // len(keywords)])
            
            except Exception as e:
                logger.error(f"Error buscando B-Roll para '{keyword}': {e}")
        
        return results[:quantity]
    
    async def _search_internal(self, keyword: str) -> List[Dict]:
        """Buscar en repositorio interno"""
        
        results = []
        keyword_lower = keyword.lower()
        
        for loop_id, loop_data in self.INTERNAL_LOOPS.items():
            # Buscar por ID o tags
            if keyword_lower in loop_id or any(keyword_lower in tag for tag in loop_data["tags"]):
                results.append({
                    "source": "internal",
                    "id": loop_id,
                    "url": loop_data["url"],
                    "duration": loop_data["duration"],
                    "tags": loop_data["tags"],
                    "relevance": 0.9
                })
        
        return results
    
    async def _search_pexels(self, keyword: str, quantity: int = 5) -> List[Dict]:
        """Buscar en Pexels API"""
        
        url = f"{self.PEXELS_API_URL}/videos/search"
        
        headers = {
            "Authorization": settings.pexels_api_key
        }
        
        params = {
            "query": keyword,
            "per_page": quantity,
            "min_duration": 1,
            "max_duration": 20
        }
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for video in data.get("videos", []):
                        # Obtener URL de mejor calidad disponible
                        video_files = video.get("video_files", [])
                        video_url = None
                        
                        # Preferir portrait (9:16) para redes sociales
                        for file in sorted(video_files, 
                                         key=lambda x: x.get("height", 0), 
                                         reverse=True):
                            if file.get("width", 0) < file.get("height", 0):
                                video_url = file["link"]
                                break
                        
                        if not video_url and video_files:
                            video_url = video_files[0]["link"]
                        
                        if video_url:
                            results.append({
                                "source": "pexels",
                                "id": str(video["id"]),
                                "url": video_url,
                                "duration": video["duration"],
                                "width": video.get("width"),
                                "height": video.get("height"),
                                "photographer": video.get("user", {}).get("name"),
                                "photographer_url": video.get("user", {}).get("url"),
                                "tags": [keyword]
                            })
                    
                    logger.info(f"Encontrados {len(results)} videos en Pexels para: {keyword}")
                    return results
                else:
                    logger.error(f"Error Pexels API: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error consultando Pexels: {e}")
            return []
    
    async def download_broll(
        self,
        video_url: str,
        output_path: str,
        source: str = "pexels"
    ) -> Optional[str]:
        """
        Descargar B-Roll
        
        Args:
            video_url: URL del video
            output_path: Ruta de salida
            source: Fuente del video
            
        Returns:
            Ruta del archivo descargado o None si falló
        """
        
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if source == "internal":
                # Los videos internos ya están en cloud storage
                logger.info(f"B-Roll interno referenciado: {video_url}")
                return video_url
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(video_url) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    logger.info(f"B-Roll descargado: {output_path}")
                    return output_path
                else:
                    logger.error(f"Error descargando B-Roll: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error en descarga de B-Roll: {e}")
            return None
    
    async def get_broll_for_script(
        self,
        script_json: Dict,
        tone: str = "viral"
    ) -> Dict[str, List[Dict]]:
        """
        Obtener B-Roll optimizado para cada sección del guión
        
        Args:
            script_json: Guión en JSON
            tone: Tono del video
            
        Returns:
            Diccionario con B-Roll por sección
        """
        
        broll_data = {}
        
        # B-Roll para el hook
        if "hook" in script_json:
            hook_keywords = script_json["hook"].get("visual_cue", "viral").split()
            broll_data["hook"] = await self.search_broll(
                keywords=hook_keywords[:2],
                quantity=3
            )
        
        # B-Roll para cada sección del body
        if "body" in script_json:
            broll_data["body_sections"] = []
            for i, section in enumerate(script_json["body"]):
                keywords = section.get("broll_keywords", [])
                section_broll = await self.search_broll(
                    keywords=keywords[:3],
                    quantity=3
                )
                broll_data["body_sections"].append({
                    "section": i,
                    "videos": section_broll
                })
        
        # B-Roll para CTA
        if "cta" in script_json:
            cta_keywords = ["call to action", "subscribe", "follow"]
            broll_data["cta"] = await self.search_broll(
                keywords=cta_keywords,
                quantity=2
            )
        
        return broll_data
    
    async def cache_broll_metadata(
        self,
        broll_data: Dict,
        cache_file: str = "broll_cache.json"
    ) -> bool:
        """Cachear metadata de B-Roll para futuros usos"""
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(broll_data, f, indent=2)
            logger.info(f"B-Roll cacheado en: {cache_file}")
            return True
        except Exception as e:
            logger.error(f"Error cacheando B-Roll: {e}")
            return False
    
    async def close(self):
        """Cerrar sesiones HTTP"""
        if self.session:
            await self.session.close()


def get_broll_manager() -> BRollManager:
    """Factory para obtener gestor de B-Roll"""
    return BRollManager()
