import streamlit as st
import requests
import time
from urllib.parse import urljoin

st.set_page_config(page_title="Clipping-AI Studio", layout="centered")

st.title("🎬 Clipping-AI — Studio (Streamlit)")
st.markdown(
    "Una interfaz ligera para interactuar con la API de Clipping-AI. Puedes ejecutar la API localmente (uvicorn/app) o usar el modo demo.")

api_url = st.text_input("API base URL", value="http://localhost:8000")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Tema / Idea", value="5 hábitos de productividad para profesionales")
    platform = st.selectbox("Plataforma", ["tiktok", "instagram", "youtube_shorts"])
with col2:
    tone = st.selectbox("Tono", ["viral", "educativo", "cómico", "motivacional"])
    duration = st.number_input("Duración (segundos)", min_value=5, max_value=180, value=30)

demo_mode = st.checkbox("Modo demo (sin llamar a la API)", value=False)

st.write("---")

if st.button("Generar video"):
    if not topic or len(topic) < 3:
        st.error("El tema es muy corto")
    else:
        if demo_mode:
            st.info("Modo demo activado — simulando generación")
            placeholder = st.empty()
            progress = st.progress(0)
            for i in range(0, 101, 10):
                progress.progress(i)
                placeholder.text(f"Estado simulado: {i}% — paso: {'rendering' if i>60 else 'generando'}")
                time.sleep(0.5)
            st.success("Video generado (modo demo)")
            st.write({
                "status": "done",
                "project_id": 1,
                "result_url": "https://example.com/videos/demo_video.mp4"
            })
        else:
            try:
                generate_endpoint = urljoin(api_url, "/api/v1/videos/generate")
                # FastAPI endpoint expects form/query parameters; we send as data
                resp = requests.post(generate_endpoint, data={
                    "topic": topic,
                    "platform": platform,
                    "tone": tone,
                    "duration": duration
                }, timeout=20)
                if resp.status_code != 200:
                    st.error(f"Error from API: {resp.status_code} — {resp.text}")
                else:
                    data = resp.json()
                    st.success("Proyecto encolado")
                    st.json(data)

                    project_id = data.get("project_id")
                    job_id = data.get("job_id")

                    if project_id:
                        st.info("Comenzando a monitorizar progreso...")
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for _ in range(60):  # timeout aprox 60*2s = 2 min
                            prog_resp = requests.get(urljoin(api_url, f"/api/v1/videos/{project_id}/progress"), timeout=10)
                            if prog_resp.status_code == 200:
                                info = prog_resp.json()
                                prog = int(info.get("progress", 0))
                                progress_bar.progress(min(max(prog, 0), 100))
                                status_text.text(f"Estado: {info.get('status')} — Paso: {info.get('current_step')} — Progreso: {prog}%")
                                if info.get("status") in ["SUCCESS", "DONE", "finished", "completed"] or prog >= 100:
                                    st.success("Render completado")
                                    st.write(info)
                                    break
                            else:
                                status_text.text(f"No se pudo obtener progreso ({prog_resp.status_code})")

                            time.sleep(2)
                        else:
                            st.warning("Tiempo de espera agotado. Verifica el estado en la API o en los logs del servidor.")

            except requests.exceptions.RequestException as e:
                st.error(f"Error conectando con la API: {e}")

st.write("---")
st.markdown("**Notas:**\n- Asegúrate de que la API (FastAPI) está corriendo en la `API base URL` y accesible.\n- Para desarrollo ejecuta `uvicorn app:app --reload --port 8000` desde la carpeta Clipping.\n- Puedes usar ngrok para exponer la API públicamente y usar esa URL aquí.")
