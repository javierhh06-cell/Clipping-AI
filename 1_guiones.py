"""
Módulo 1: Generador de Guiones para Clips Virales
Utiliza Google Generative AI (Gemini) para crear guiones optimizados para redes sociales
"""

import google.generativeai as genai
import json
from typing import Dict, List
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class GuionGenerator:
    """Generador de guiones para clips virales usando IA"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializar el generador con la clave API
        
        Args:
            api_key: Clave de la API de Google Generative AI
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY no encontrada en variables de entorno")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generar_guion(self, tema: str, plataforma: str = "tiktok", duracion: int = 30, 
                      tono: str = "viral") -> Dict:
        """
        Generar un guión para un clip viral
        
        Args:
            tema: Tema del clip (ej: "consejos de productividad", "receta rápida")
            plataforma: Red social destino (tiktok, instagram, youtube_shorts)
            duracion: Duración del clip en segundos
            tono: Tono del guión (viral, educativo, cómico, motivacional)
            
        Returns:
            Diccionario con el guión generado
        """
        
        prompt = self._construir_prompt(tema, plataforma, duracion, tono)
        
        try:
            response = self.model.generate_content(prompt)
            guion = self._parsear_respuesta(response.text, tema, plataforma, duracion)
            return guion
        except Exception as e:
            print(f"Error al generar guión: {e}")
            return None
    
    def _construir_prompt(self, tema: str, plataforma: str, duracion: int, tono: str) -> str:
        """Construir el prompt para la IA"""
        
        instrucciones_plataforma = {
            "tiktok": "Optimizado para TikTok: máximo impacto en 15-60 segundos, gancho en primeros 3 segundos",
            "instagram": "Optimizado para Instagram Reels: énfasis en lo visual, transiciones rápidas, 15-90 segundos",
            "youtube_shorts": "Optimizado para YouTube Shorts: contenido más sustancial, 15-60 segundos, call-to-action claro"
        }
        
        instruccion = instrucciones_plataforma.get(plataforma, instrucciones_plataforma["tiktok"])
        
        prompt = f"""
Eres un experto en crear guiones para clips virales en redes sociales.

TEMA: {tema}
PLATAFORMA: {plataforma}
DURACIÓN: {duracion} segundos aproximadamente
TONO: {tono}

RESTRICCIONES:
- {instruccion}
- El guión debe ser atractivo y captar atención inmediatamente
- Usar un lenguaje natural y conversacional
- Incluir elementos de sorpresa, humor o valor
- Optimizar para máxima reproducción y engagement

FORMATO DE RESPUESTA (JSON):
{{
    "gancho": "Primera frase para captar atención (máximo 10 palabras)",
    "desarrollo": ["Punto 1", "Punto 2", "Punto 3"],
    "cierre": "Conclusión con call-to-action",
    "detalles_visuales": ["Visual 1", "Visual 2", "Visual 3"],
    "duracion_estimada": "Tiempo en segundos para cada sección",
    "consejos_produccion": ["Consejo 1", "Consejo 2"]
}}

Genera un guión viral y atractivo:
"""
        return prompt
    
    def _parsear_respuesta(self, respuesta: str, tema: str, plataforma: str, duracion: int) -> Dict:
        """Parsear la respuesta de la IA"""
        
        try:
            # Intentar extraer JSON de la respuesta
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}') + 1
            if inicio != -1 and fin > inicio:
                json_str = respuesta[inicio:fin]
                guion = json.loads(json_str)
            else:
                # Si no hay JSON válido, crear estructura manualmente
                guion = {
                    "gancho": "Contenido viral",
                    "desarrollo": [respuesta],
                    "cierre": "Acción recomendada",
                    "detalles_visuales": ["Visual atractivo"],
                    "duracion_estimada": f"{duracion}s",
                    "consejos_produccion": ["Usa buena iluminación", "Agrégale música de fondo"]
                }
        except json.JSONDecodeError:
            guion = {
                "gancho": "Contenido viral",
                "desarrollo": [respuesta],
                "cierre": "Acción recomendada",
                "detalles_visuales": ["Visual atractivo"],
                "duracion_estimada": f"{duracion}s",
                "consejos_produccion": []
            }
        
        # Agregar metadatos
        guion["tema"] = tema
        guion["plataforma"] = plataforma
        guion["duracion"] = duracion
        
        return guion
    
    def generar_multiples_variantes(self, tema: str, cantidad: int = 3, 
                                   plataforma: str = "tiktok") -> List[Dict]:
        """
        Generar múltiples variantes del mismo tema
        
        Args:
            tema: Tema base para las variantes
            cantidad: Número de variantes a generar
            plataforma: Red social destino
            
        Returns:
            Lista de guiones generados
        """
        guiones = []
        tonos = ["viral", "educativo", "cómico"][:cantidad]
        
        for i, tono in enumerate(tonos):
            print(f"Generando variante {i+1}/{cantidad}...")
            guion = self.generar_guion(tema, plataforma, tono=tono)
            if guion:
                guiones.append(guion)
        
        return guiones


# Función auxiliar para uso fácil
def crear_generador(api_key: str = None) -> GuionGenerator:
    """Crear una instancia del generador de guiones"""
    return GuionGenerator(api_key)


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        generador = GuionGenerator()
        
        # Generar un guión simple
        guion = generador.generar_guion(
            tema="Rutina matinal para ser más productivo",
            plataforma="tiktok",
            duracion=30,
            tono="viral"
        )
        
        if guion:
            print("\n=== GUIÓN GENERADO ===")
            print(json.dumps(guion, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error: {e}")
        print("Asegúrate de tener configurada tu GOOGLE_API_KEY en el archivo .env")
