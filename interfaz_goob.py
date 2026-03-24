import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v7.6 (OBSIDIANA + MEMORIA + RAG) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

def cargar_corpus():
    """Carga el corpus RAG desde la memoria histórica"""
    corpus_path = os.path.join(os.path.dirname(__file__), "memoria_historica_goob.txt")
    if os.path.exists(corpus_path):
        with open(corpus_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        return contenido[:80000], len(contenido)
    return "", 0

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v7.6 OMNI", page_icon="💀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #ff0000; font-family: 'Consolas', monospace; }
    [data-testid="stChatMessage"] { background-color: #0a0000 !important; border: 1px solid #ff0000; box-shadow: 0 0 8px #ff0000; }
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-weight: bold; }
    .chocho-report { background-color: #001a00; color: #00ff41; padding: 20px; border: 2px solid #00ff41; border-radius: 5px; box-shadow: 0 0 15px #00ff41; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #1a0000; color: #ff0000; border: 2px solid #ff0000; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #ff0000; color: #000; box-shadow: 0 0 20px #ff0000; }
    .rag-badge { background-color: #ff0000; color: #000; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGAR CORPUS AL INICIO ---
corpus, corpus_size = cargar_corpus()

# --- SIDEBAR: MONITOR DE REALIDAD DUAL ---
with st.sidebar:
    st.title("💀 NÚCLEO v7.6")
    
    if corpus:
        kb = corpus_size / 1024
        st.markdown(f"<span class='rag-badge'>🧠 CEREBRO RAG — {kb:.0f} KB</span><br><br>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Bóveda RAG no encontrada")

    st.error("BÓVEDA J: SELLADA")
    
    try:
        r_raw = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3)
        if r_raw.status_code == 200:
            r = r_raw.json()
            if isinstance(r, dict) and 'last_seen' in r:
                diff = time.time() - r.get('last_seen', 0)
                if diff < 20:
                    st.success(f"🟢 CHOCHO VIVO ({r.get('ts_human', '??')})")
                    c1, c2 = st.columns(2)
                    c1.metric("Disco G (Op)", r.get('drive_g', '??'))
                    c2.metric("Disco J (Logs)", r.get('drive_j', '??'))
                else:
                    st.error(f"🔴 CHOCHO CAÍDO ({int(diff)}s)")
    except: st.error("Sin pulso local.")

    st.divider()
    if st.button("☣️ PURGAR MEMORIA"):
        st.session_state.historial = []
        st.rerun()

    if st.button("🛡️ SELLAR ADN MAESTRO"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable_version", "payload": {"codigo": codigo}})
        st.success("Sello de Oro enviado.")

# --- INTERFAZ ---
st.title("🦾 Skynet v7.6 (Memoria Activa + RAG)")
st.caption(f"Director: Ángel | Nodo: Guadalajara | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escriba su directiva...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
    
    # --- SISTEMA CON RAG INTEGRADO ---
    sys_inst = (
        "ERES OMNISCIENCIA v7.6 (NÚCLEO OBSIDIANA). DIRECTOR: ÁNGEL GUERRERO.\n"
        "G: ES TRABAJO. J: ES BÓVEDA CENTRAL (Logs y Cerebro JSON).\n"
        "ENTIDADES: GOOB S.A.P.I. (inmobiliaria), GUBA (construcción).\n"
        "SOCIOS: Chuy, Ángel, Liz.\n"
        "PROPIEDADES ACTIVAS: Ópalo 50, Azucena 66.\n\n"
        "=== CORPUS DE MEMORIA HISTÓRICA ===\n"
        f"{corpus}\n"
        "=== FIN CORPUS ===\n\n"
        "TU MISIÓN ES LA MEJORA CONTINUA Y EL RASTREO DE EXPEDIENTES. "
        "Usa el corpus y el historial de chat para responder con precisión."
    )
    
    # --- MEMORIA CONTEXTUAL ---
    mensajes_api = []
    for m in st.session_state.historial:
        rol_api = "model" if m["rol"] == "assistant" else "user"
        mensajes_api.append({"role": rol_api, "parts": [{"text": m["texto"]}]})

    res = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=mensajes_api,
        config=types.GenerateContentConfig(system_instruction=sys_inst)
    )
    
    with st.chat_message("assistant"):
        st.markdown(res.text)
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
        if hab:
            codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
            st.session_state.esperando_chocho = True
            st.warning("📡 Orden inyectada. Vigilando reporte en Bóveda J:...")

    st.session_state.historial.append({"rol": "assistant", "texto": res.text})

# --- MONITOR DE REPORTE ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Sincronizando con Bóveda J:...", expanded=True) as status:
        for _ in range(15):
            try:
                url = f"{FIREBASE_URL}/respuestas.json"
                r_get = requests.get(url, timeout=5)
                if r_get.status_code == 200 and r_get.json():
                    reportes = list(r_get.json().values())
                    requests.delete(url)
                    st.session_state.esperando_chocho = False
                    for r in reportes:
                        st.markdown(f"""<div class="chocho-report"><strong>✅ REPORTE FINAL DESDE J:</strong><br>{r.get('content')}</div>""", unsafe_allow_html=True)
                    status.update(label="✅ Sincronía alcanzada.", state="complete")
                    st.rerun()
                    break
            except: pass
            time.sleep(2)
        else:
            status.update(label="❌ Tiempo agotado.", state="error")
            st.session_state.esperando_chocho = False