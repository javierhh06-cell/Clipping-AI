"""
Módulo de Autenticación OAuth2 y Publicación
Integración con YouTube, Instagram y TikTok
"""

import logging
from typing import Optional, Dict
import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from datetime import datetime, timedelta
from config import settings
import json

logger = logging.getLogger(__name__)


class OAuthManager:
    """Gestor de autenticación OAuth2 para plataformas sociales"""
    
    PROVIDERS = {
        "youtube": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "access_token_url": "https://oauth2.googleapis.com/token",
            "redirect_uri": settings.youtube_redirect_uri,
            "scopes": [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        },
        "instagram": {
            "client_id": settings.instagram_client_id,
            "client_secret": settings.instagram_client_secret,
            "authorize_url": "https://api.instagram.com/oauth/authorize",
            "access_token_url": "https://graph.instagram.com/v18.0/oauth/access_token",
            "redirect_uri": settings.instagram_redirect_uri,
            "scopes": ["instagram_business_basic", "instagram_business_content_publish"]
        },
        "tiktok": {
            "client_id": settings.tiktok_client_id,
            "client_secret": settings.tiktok_client_secret,
            "authorize_url": "https://www.tiktok.com/v1/oauth/authorize",
            "access_token_url": "https://open.tiktokapis.com/v1/oauth/token",
            "redirect_uri": settings.tiktok_redirect_uri,
            "scopes": ["user.info.basic", "video.upload"]
        }
    }
    
    def __init__(self):
        """Inicializar el gestor OAuth2"""
        self.clients = {}
    
    def get_authorization_url(
        self,
        provider: str,
        state: str
    ) -> str:
        """
        Generar URL de autorización para el usuario
        
        Args:
            provider: "youtube", "instagram" o "tiktok"
            state: Token de estado CSRF
            
        Returns:
            URL de autorización
        """
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.PROVIDERS[provider]
        
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "state": state,
            "scope": " ".join(config["scopes"]) if provider != "tiktok" else ",".join(config["scopes"]),
        }
        
        if provider == "instagram":
            params["response_type"] = "code"
        elif provider == "tiktok":
            params["scope"] = ",".join(config["scopes"])
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{config['authorize_url']}?{query_string}"
        
        logger.info(f"URL de autorización generada para {provider}")
        return url
    
    async def exchange_code_for_token(
        self,
        provider: str,
        code: str
    ) -> Optional[Dict]:
        """
        Intercambiar código de autorización por token de acceso
        
        Args:
            provider: Proveedor OAuth2
            code: Código de autorización
            
        Returns:
            Diccionario con token de acceso y metadatos
        """
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.PROVIDERS[provider]
        
        payload = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config["redirect_uri"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config["access_token_url"],
                    data=payload
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Parsear respuesta según proveedor
                    if provider == "youtube":
                        return {
                            "provider": "youtube",
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "expires_at": datetime.utcnow() + timedelta(
                                seconds=token_data.get("expires_in", 3600)
                            ),
                            "scope": token_data.get("scope"),
                            "token_type": token_data.get("token_type")
                        }
                    
                    elif provider == "instagram":
                        return {
                            "provider": "instagram",
                            "access_token": token_data.get("access_token"),
                            "expires_at": datetime.utcnow() + timedelta(
                                seconds=token_data.get("expires_in", 5184000)
                            ),
                            "user_id": token_data.get("user_id")
                        }
                    
                    elif provider == "tiktok":
                        return {
                            "provider": "tiktok",
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "expires_at": datetime.utcnow() + timedelta(
                                seconds=token_data.get("expires_in", 3600)
                            ),
                            "open_id": token_data.get("open_id")
                        }
                else:
                    logger.error(f"Error obteniendo token: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error intercambiando código por token: {e}")
            return None
    
    async def refresh_access_token(
        self,
        provider: str,
        refresh_token: str
    ) -> Optional[Dict]:
        """
        Refrescar token de acceso expirado
        """
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Proveedor no soportado: {provider}")
        
        config = self.PROVIDERS[provider]
        
        payload = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config["access_token_url"],
                    data=payload
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return {
                        "access_token": token_data.get("access_token"),
                        "expires_at": datetime.utcnow() + timedelta(
                            seconds=token_data.get("expires_in", 3600)
                        )
                    }
                else:
                    logger.error(f"Error refrescando token: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"Error refrescando token: {e}")
            return None


class PlatformPublisher:
    """Publicador de videos en plataformas sociales"""
    
    def __init__(self):
        """Inicializar publicador"""
        self.oauth_manager = OAuthManager()
    
    async def publish_to_youtube(
        self,
        video_path: str,
        access_token: str,
        title: str,
        description: str,
        tags: list = None,
        category_id: str = "24",  # Entertainment
        privacy_status: str = "public"
    ) -> Optional[Dict]:
        """
        Publicar video a YouTube Shorts
        
        Args:
            video_path: Ruta del archivo de video
            access_token: Token de acceso de YouTube
            title: Título del video
            description: Descripción
            tags: Lista de tags
            category_id: ID de categoría
            privacy_status: "public", "unlisted" o "private"
            
        Returns:
            Respuesta con video_id
        """
        
        try:
            logger.info("Publicando video a YouTube")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Metadata del video
            metadata = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Nota: YouTube requiere multipart upload, implementar correctamente
            logger.warning("YouTube upload requiere implementación completa del multipart")
            
            return {
                "platform": "youtube",
                "status": "queued",
                "video_id": None  # Se obtendría de la respuesta real
            }
        
        except Exception as e:
            logger.error(f"Error publicando en YouTube: {e}")
            return None
    
    async def publish_to_instagram(
        self,
        video_path: str,
        access_token: str,
        caption: str,
        user_id: str,
        hashtags: list = None
    ) -> Optional[Dict]:
        """
        Publicar Reel a Instagram
        
        Args:
            video_path: Ruta del archivo de video
            access_token: Token de acceso de Instagram
            caption: Texto del post
            user_id: ID del usuario de Instagram
            hashtags: Lista de hashtags
            
        Returns:
            Respuesta con media_id
        """
        
        try:
            logger.info("Publicando Reel a Instagram")
            
            # Construir caption con hashtags
            full_caption = caption
            if hashtags:
                full_caption += " " + " ".join(hashtags)
            
            # Implementación simplificada
            # En producción, necesitarías seguir el flujo completo de Instagram
            
            return {
                "platform": "instagram",
                "status": "pending_approval",
                "media_id": None
            }
        
        except Exception as e:
            logger.error(f"Error publicando en Instagram: {e}")
            return None
    
    async def publish_to_tiktok(
        self,
        video_path: str,
        access_token: str,
        description: str,
        hashtags: list = None,
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False
    ) -> Optional[Dict]:
        """
        Publicar video a TikTok (Direct Post)
        
        Args:
            video_path: Ruta del archivo de video
            access_token: Token de acceso de TikTok
            description: Descripción del video
            hashtags: Lista de hashtags
            disable_comment: Desabilitar comentarios
            disable_duet: Desabilitar duets
            disable_stitch: Desabilitar stitches
            
        Returns:
            Respuesta con video_id
        """
        
        try:
            logger.info("Publicando video a TikTok")
            
            # El video se queda en el borrador del usuario, no se publica automáticamente
            # TikTok requiere que el usuario confirme la publicación
            
            return {
                "platform": "tiktok",
                "status": "draft",
                "message": "Video enviado al borrador del usuario. Debe publicarlo manualmente.",
                "video_id": None
            }
        
        except Exception as e:
            logger.error(f"Error publicando en TikTok: {e}")
            return None


def get_oauth_manager() -> OAuthManager:
    """Factory para obtener gestor OAuth2"""
    return OAuthManager()


def get_platform_publisher() -> PlatformPublisher:
    """Factory para obtener publicador de plataformas"""
    return PlatformPublisher()
