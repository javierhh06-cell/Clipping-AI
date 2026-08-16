"""
Módulo 2: Generador de Audio (Text-to-Speech)
Convierte los guiones a audio usando edge-tts
"""

import asyncio
import edge_tts
from pathlib import Path
import os
from typing import List


class AudioGenerator:
    """Generador de audio para guiones"""
    
    VOCES_DISPONIBLES = {
        "es-ES": {
            "femenino": "es-ES-ElviraNeural",
            "masculino": "es-ES-AlvaroNeural"
        },
        "es-MX": {
            "femenino": "es-MX-DoloresNeural",
            "masculino": "es-MX-JorgeNeural"
        },
        "es-AR": {
            "femenino": "es-AR-ElenaNeural",
            "masculino": "es-AR-TomasNeural"
        }
    }
    
    def __init__(self, lenguaje: str = "es-ES", genero: str = "femenino", velocidad: float = 1.0):
        """
        Inicializar el generador de audio
        
        Args:
            lenguaje: Código de lenguaje (es-ES, es-MX, es-AR)
            genero: Género de la voz (femenino, masculino)
            velocidad: Velocidad de reproducción (0.5 - 2.0)
        """
        self.lenguaje = lenguaje
        self.genero = genero
        self.velocidad = velocidad
        self.voz = self._obtener_voz()
        
    def _obtener_voz(self) -> str:
        """Obtener el nombre de la voz según configuración"""
        if self.lenguaje in self.VOCES_DISPONIBLES:
            return self.VOCES_DISPONIBLES[self.lenguaje].get(self.genero, "es-ES-ElviraNeural")
        return "es-ES-ElviraNeural"
    
    async def generar_audio_async(self, texto: str, ruta_salida: str = "output.mp3") -> bool:
        """
        Generar audio de manera asincrónica
        
        Args:
            texto: Texto a convertir en audio
            ruta_salida: Ruta donde guardar el archivo MP3
            
        Returns:
            True si fue exitoso, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
            
            # Crear comunicator y generar audio
            communicate = edge_tts.Communicate(
                text=texto,
                voice=self.voz,
                rate=f"{int((self.velocidad - 1) * 50 + 0):+d}%"  # Convertir velocidad a porcentaje
            )
            
            await communicate.save(ruta_salida)
            print(f"✓ Audio guardado en: {ruta_salida}")
            return True
            
        except Exception as e:
            print(f"✗ Error al generar audio: {e}")
            return False
    
    def generar_audio(self, texto: str, ruta_salida: str = "output.mp3") -> bool:
        """
        Generar audio (versión síncrona)
        
        Args:
            texto: Texto a convertir en audio
            ruta_salida: Ruta donde guardar el archivo MP3
            
        Returns:
            True si fue exitoso, False en caso contrario
        """
        return asyncio.run(self.generar_audio_async(texto, ruta_salida))
    
    async def generar_multiples_audios_async(self, textos: List[tuple], 
                                            directorio: str = "audios") -> List[str]:
        """
        Generar múltiples audios en paralelo
        
        Args:
            textos: Lista de tuplas (nombre, texto)
            directorio: Directorio donde guardar los archivos
            
        Returns:
            Lista de rutas de archivos generados
        """
        # Crear directorio
        Path(directorio).mkdir(parents=True, exist_ok=True)
        
        tareas = []
        rutas = []
        
        for nombre, texto in textos:
            ruta = os.path.join(directorio, f"{nombre}.mp3")
            rutas.append(ruta)
            
            communicate = edge_tts.Communicate(
                text=texto,
                voice=self.voz,
                rate=f"{int((self.velocidad - 1) * 50 + 0):+d}%"
            )
            tareas.append(communicate.save(ruta))
        
        # Ejecutar todas las tareas en paralelo
        await asyncio.gather(*tareas)
        print(f"✓ {len(rutas)} archivos de audio generados en: {directorio}")
        
        return rutas
    
    def generar_multiples_audios(self, textos: List[tuple], 
                                 directorio: str = "audios") -> List[str]:
        """Generar múltiples audios (versión síncrona)"""
        return asyncio.run(self.generar_multiples_audios_async(textos, directorio))


if __name__ == "__main__":
    # Ejemplo de uso
    generador = AudioGenerator(lenguaje="es-ES", genero="femenino")
    
    texto = """Hola, hoy te traigo un consejo increíble para tu productividad. 
    Si implementas esta rutina matinal, tu día será completamente diferente. ¡No te lo pierdas!"""
    
    generador.generar_audio(texto, "ejemplo_audio.mp3")
