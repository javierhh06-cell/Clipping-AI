"""
Script Principal: Generador Completo de Clips Virales
Integra generación de guiones y audio en un flujo completo
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# Importar módulos locales
from 1_guiones import GuionGenerator
from 2_audio import AudioGenerator

# Cargar variables de entorno
load_dotenv()


class GeneradorClipsVirales:
    """Orquestador principal para generar clips virales completos"""
    
    def __init__(self, api_key: str = None):
        """Inicializar el generador de clips"""
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.guion_gen = GuionGenerator(self.api_key)
        self.audio_gen = AudioGenerator()
        
        # Crear estructura de directorios
        self.crear_estructura_directorios()
    
    def crear_estructura_directorios(self):
        """Crear estructura de directorios para el proyecto"""
        directorios = [
            "guiones",
            "audios",
            "videos",
            "proyectos"
        ]
        for dir_name in directorios:
            Path(dir_name).mkdir(exist_ok=True)
    
    def generar_clip_completo(self, tema: str, plataforma: str = "tiktok", 
                             duracion: int = 30, tono: str = "viral",
                             generar_audio: bool = True) -> Optional[Dict]:
        """
        Generar un clip viral completo con guión y audio
        
        Args:
            tema: Tema del clip
            plataforma: Red social destino
            duracion: Duración en segundos
            tono: Tono del guión
            generar_audio: Si genera el audio o solo el guión
            
        Returns:
            Diccionario con información del clip generado
        """
        print(f"\n{'='*60}")
        print(f"Generando clip viral: {tema}")
        print(f"{'='*60}\n")
        
        # Paso 1: Generar guión
        print("📝 Generando guión...")
        guion = self.guion_gen.generar_guion(tema, plataforma, duracion, tono)
        
        if not guion:
            print("✗ Error al generar el guión")
            return None
        
        # Guardar guión
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_proyecto = f"{tema[:20].replace(' ', '_')}_{fecha}"
        ruta_guion = f"guiones/{nombre_proyecto}.json"
        
        with open(ruta_guion, 'w', encoding='utf-8') as f:
            json.dump(guion, f, ensure_ascii=False, indent=2)
        print(f"✓ Guión guardado: {ruta_guion}")
        
        # Paso 2: Generar audio
        ruta_audio = None
        if generar_audio:
            print("\n🎙️ Generando audio...")
            texto_completo = self._construir_texto_audio(guion)
            ruta_audio = f"audios/{nombre_proyecto}.mp3"
            
            if self.audio_gen.generar_audio(texto_completo, ruta_audio):
                print(f"✓ Audio guardado: {ruta_audio}")
            else:
                print("⚠ Error al generar el audio")
                ruta_audio = None
        
        # Crear resumen del proyecto
        resumen = {
            "nombre": nombre_proyecto,
            "tema": tema,
            "plataforma": plataforma,
            "duracion": duracion,
            "tono": tono,
            "fecha_creacion": datetime.now().isoformat(),
            "ruta_guion": ruta_guion,
            "ruta_audio": ruta_audio,
            "guion": guion
        }
        
        # Guardar resumen
        ruta_resumen = f"proyectos/{nombre_proyecto}.json"
        with open(ruta_resumen, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"✓ Proyecto guardado: {ruta_resumen}")
        
        return resumen
    
    def _construir_texto_audio(self, guion: Dict) -> str:
        """Construir texto continuo para el audio desde el guión"""
        partes = []
        
        # Gancho
        if "gancho" in guion:
            partes.append(guion["gancho"])
        
        # Desarrollo
        if "desarrollo" in guion:
            for punto in guion["desarrollo"]:
                partes.append(punto)
        
        # Cierre
        if "cierre" in guion:
            partes.append(guion["cierre"])
        
        return " ".join(partes)
    
    def generar_variantes(self, tema: str, cantidad: int = 3, 
                         plataforma: str = "tiktok") -> list:
        """
        Generar múltiples variantes de un clip
        
        Args:
            tema: Tema base
            cantidad: Número de variantes
            plataforma: Red social destino
            
        Returns:
            Lista de resúmenes de proyectos
        """
        proyectos = []
        
        for i in range(cantidad):
            clip = self.generar_clip_completo(
                tema=f"{tema} (Variante {i+1})",
                plataforma=plataforma,
                generar_audio=True
            )
            if clip:
                proyectos.append(clip)
        
        return proyectos


def main():
    """Función principal con interfaz interactiva"""
    
    print("\n" + "="*60)
    print("🎬 GENERADOR DE CLIPS VIRALES CON IA")
    print("="*60)
    
    try:
        # Inicializar generador
        generador = GeneradorClipsVirales()
        
        while True:
            print("\n📋 Opciones disponibles:")
            print("1. Generar un clip viral")
            print("2. Generar variantes de un tema")
            print("3. Salir")
            
            opcion = input("\nSelecciona una opción (1-3): ").strip()
            
            if opcion == "1":
                tema = input("\n📝 Ingresa el tema del clip: ").strip()
                if not tema:
                    print("⚠ El tema no puede estar vacío")
                    continue
                
                print("\n🎯 Plataformas disponibles:")
                print("1. TikTok")
                print("2. Instagram")
                print("3. YouTube Shorts")
                plataforma_opcion = input("Selecciona plataforma (1-3): ").strip()
                
                plataformas = {
                    "1": "tiktok",
                    "2": "instagram",
                    "3": "youtube_shorts"
                }
                plataforma = plataformas.get(plataforma_opcion, "tiktok")
                
                clip = generador.generar_clip_completo(
                    tema=tema,
                    plataforma=plataforma,
                    duracion=30,
                    generar_audio=True
                )
                
                if clip:
                    print(f"\n✓ Clip generado exitosamente!")
                    print(f"📁 Guión: {clip['ruta_guion']}")
                    print(f"🎙️ Audio: {clip['ruta_audio']}")
            
            elif opcion == "2":
                tema = input("\n📝 Ingresa el tema base: ").strip()
                cantidad_str = input("¿Cuántas variantes deseas? (1-5): ").strip()
                
                try:
                    cantidad = int(cantidad_str)
                    cantidad = max(1, min(5, cantidad))
                except ValueError:
                    cantidad = 3
                
                print(f"\n⏳ Generando {cantidad} variantes...")
                variantes = generador.generar_variantes(tema, cantidad)
                print(f"\n✓ {len(variantes)} variantes generadas exitosamente!")
            
            elif opcion == "3":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("⚠ Opción no válida")
    
    except ValueError as e:
        print(f"\n✗ Error de configuración: {e}")
        print("Asegúrate de tener configurada tu GOOGLE_API_KEY en el archivo .env")
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")


if __name__ == "__main__":
    main()
