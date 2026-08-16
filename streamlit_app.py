import os
import importlib.util
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def load_module_from_file(module_name: str, file_path: str):
    """Carga un módulo Python desde una ruta de archivo en disco."""
    path = Path(file_path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el módulo desde: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GuionGenerator = load_module_from_file(
    "guion_generator_module",
    str(Path(__file__).with_name("1_guiones.py")),
).GuionGenerator

# URL pública de referencia del frontend web en Streamlit.
# Sustituir por la URL real cuando se publique la app en Streamlit Cloud.
STREAMLIT_PUBLIC_URL = "https://tu-proyecto.streamlit.app"
REFERENCE_URL_NOTE = (
    "URL pública de referencia del proyecto en Streamlit: "
    f"{STREAMLIT_PUBLIC_URL}. Guardar esta URL como referencia por si se pierde."
)

st.set_page_config(page_title="Generador de Clips Virales", page_icon="🎬", layout="wide")

st.title("🎬 Generador de Clips Virales")
st.caption(REFERENCE_URL_NOTE)

st.markdown("---")

with st.sidebar:
    st.header("Configuración")
    tema = st.text_input("Tema del clip", value="Rutina matinal para ser más productivo")
    plataforma = st.selectbox("Plataforma", ["tiktok", "instagram", "youtube_shorts"])
    duracion = st.slider("Duración estimada (segundos)", 15, 60, 30)
    tono = st.selectbox("Tono", ["viral", "educativo", "cómico", "motivacional"])
    generar = st.button("Generar guion", type="primary")

if generar:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass

    if not api_key:
        st.error(
            "No se encontró GOOGLE_API_KEY. Añádela en el archivo .env local o en Streamlit Secrets "
            "del despliegue en la nube."
        )
        st.stop()

    try:
        with st.spinner("Generando guion con IA..."):
            generator = GuionGenerator(api_key=api_key)
            guion = generator.generar_guion(
                tema=tema,
                plataforma=plataforma,
                duracion=duracion,
                tono=tono,
            )

        if not guion:
            st.warning("La IA no devolvió un guion válido. Revisa la clave API y el modelo.")
            st.stop()

        st.success("Guion generado correctamente")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Gancho")
            st.write(guion.get("gancho", "-"))

            st.subheader("Desarrollo")
            for i, item in enumerate(guion.get("desarrollo", []), start=1):
                st.write(f"{i}. {item}")

            st.subheader("Cierre")
            st.write(guion.get("cierre", "-"))

        with col2:
            st.subheader("Detalles visuales")
            for item in guion.get("detalles_visuales", []):
                st.write("- " + item)

            st.subheader("Consejos de producción")
            for item in guion.get("consejos_produccion", []):
                st.write("- " + item)

            st.subheader("Metadatos")
            st.json({
                "tema": guion.get("tema", tema),
                "plataforma": guion.get("plataforma", plataforma),
                "duracion": guion.get("duracion", duracion),
                "tono": tono,
            })

    except Exception as e:
        st.error(f"Error al generar el guion: {e}")
else:
    st.info("Introduce el tema y pulsa el botón para generar un guion viral.")

st.markdown("---")
st.caption("Proyecto preparado para desplegar en Streamlit Cloud.")
