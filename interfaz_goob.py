import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json, io, contextlib
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v8.5 (RAG ACTIVO) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

def cargar_corpus():
    """Carga el corpus RAG desde memoria_historica_goob.txt"""
    corpus_path = os.path.join(os.path.dirname(__file__), "memoria_historica_goob.txt")
    if os.path.exists(corpus_path):
        with open(corpus_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        # Primeros 80KB para no saturar el contexto de Gemini
        return contenido[:80000], len(contenido)
    return "", 0

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v8.5 RAG", page_icon="🧬", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f8f9fa; color: #212529; font-family: 'Segoe UI', sans-serif; }
[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #dee2e6; }
h1, h2, h3 { color: #1a73e8; font-weight: 700; }
.stChatMessage {
    border-radius: 15px; border: none; padding: 20px; margin-bottom: 15px;
    background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.disk-card {
    background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px;
    border-radius: 12px; text-align: center; margin-bottom: 12px;
}
.status-online { color: #28a745; font-weight: 700; font-size: 16px; }
.chocho-report {
    background-color: #e6ffed; color: #155724; padding: 25px;
    border: 1px solid #c3e6cb; border-radius: 12px;
    font-family: 'Segoe UI', sans-serif; font-size: 15px;
    white-space: pre-wrap; box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    margin-top: 20px;
}
.rag-badge {
    background-color: #1a73e8; color: white; padding: 4px 10px;
    border-radius: 20px; font-size: 12px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --- CARGAR CORPUS AL INICIO ---
corpus, corpus_size = cargar_corpus()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🧬 NÚCLEO v8.5</h2>", unsafe_allow_html=True)
    st.caption(f"Nodo Guadalajara | {obtener_hora_gdl()}")

    # Estado RAG
    if corpus:
        kb = corpus_size / 1024
        st.markdown(f"<span class='rag-badge'>🧠 RAG ACTIVO — {kb:.0f} KB</span>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Corpus no encontrado")

    st.write("")

    try:
        r_chocho = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r_chocho:
            diff = time.time() - r_chocho.get('last_seen', 0)
            if diff < 20:
                st.markdown(f"**ESTADO:** <span class='status-online'>● ONLINE</span>", unsafe_allow_html=True)
                st.write("---")
                discos = r_chocho.get('discos', {})
                cols = st.columns(3)
                for i, (l, s) in enumerate(discos.items()):
                    color = "status-online" if s == "OK" else "color: #dc3545;"
                    cols[i % 3].markdown(f"<div class='disk-card'><b>{l}:</b><br><span class='{color}'>{s}</span></div>", unsafe_allow_html=True)
            else:
                st.error(f"Chocho desconectado ({int(diff)}s)")
    except:
        st.error("Error de Red.")

    st.divider()

    if st.button("📌 SELLAR VERSIÓN ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            code = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable_version", "payload": {"codigo": code}})
        st.success("Sello guardado.")

    if st.button("🔄 ACTUALIZAR DESDE GITHUB"):
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "force_github_sync"})
        st.info("Sincronizando...")

    if st.button("🔁 RECARGAR CORPUS"):
        corpus, corpus_size = cargar_corpus()
        st.success(f"Corpus recargado: {corpus_size/1024:.0f} KB")

# --- CUERPO ---
st.title("👨‍💼 Centro de Mando: Omni 8.5 RAG")

if "historial" not in st.session_state:
    st.session_state.historial = []
if "esperando_chocho" not in st.session_state:
    st.session_state.esperando_chocho = False

for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]):
        st.markdown(m["texto"])

pregunta = st.chat_input("Directiva para OMNISCIENCIA...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])

        # System prompt CON corpus RAG inyectado
        sys_inst = (
            "ERES OMNISCIENCIA v8.5. DIRECTOR: ÁNGEL GUERRERO (ingeniero mecatrónico, GDL).\n"
            "FILOSOFÍA: Ingeniería del Caos.\n"
            "ENTIDADES: GOOB S.A.P.I. (inmobiliaria), GUBA (construcción), "
            "Neurodivergente A.C. (salud mental), Neurosoma 42.0 (aceites/bálsamos).\n"
            "SOCIOS: Chuy (50% acciones, 40% utilidades), Ángel (30%), Liz (20%).\n"
            "PROPIEDADES ACTIVAS: Ópalo 50, Azucena 66.\n\n"
            "=== CORPUS DE MEMORIA HISTÓRICA DEL NEGOCIO ===\n"
            f"{corpus}\n"
            "=== FIN CORPUS ===\n\n"
            "INSTRUCCIONES:\n"
            "- Usa el corpus para responder con precisión sobre el negocio.\n"
            "- Para acceso físico a discos locales usa <nueva_habilidad>código python</nueva_habilidad>.\n"
            "- Respuestas directas, técnicas, sin relleno.\n"
            "- PROHIBIDO usar <mutacion_skynet> para respuestas de texto."
        )

        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=pregunta,
            config=types.GenerateContentConfig(system_instruction=sys_inst)
        )

        with st.chat_message("assistant"):
            st.markdown(res.text)

        # Filtro mutación ADN
        sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
        if sky:
            adn = sky.group(1).strip().replace("```python", "").replace("```", "")
            if "import streamlit" in adn and "st.set_page_config" in adn:
                with open(__file__, "w", encoding="utf-8") as f:
                    f.write(adn)
                st.info("ADN Mutado. Reiniciando...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⚠️ Mutación bloqueada: Formato inválido.")

        # Habilidad para Chocho
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
        if hab:
            codigo_hab = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo_hab}})
            st.session_state.esperando_chocho = True
            st.toast("Orden enviada a Chocho...")

        st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla de Matriz: {e}")

# Monitor de respuestas Chocho
if st.session_state.esperando_chocho:
    with st.status("🔍 Chocho operando...") as status:
        for _ in range(15):
            r = requests.get(f"{FIREBASE_URL}/respuestas.json").json()
            if r:
                data = list(r.values())[0]
                requests.delete(f"{FIREBASE_URL}/respuestas.json")
                st.session_state.esperando_chocho = False
                st.markdown(f"<div class='chocho-report'>{data.get('content')}</div>", unsafe_allow_html=True)
                status.update(label="Reporte recibido.", state="complete")
                break
            time.sleep(2)