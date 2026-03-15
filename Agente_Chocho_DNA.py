import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v7.8 (NÚCLEO DE RECUPERACIÓN) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v7.8 MEMORIA", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #ff0000; font-family: 'Consolas', monospace; }
    [data-testid="stChatMessage"] { background-color: #050505 !important; border: 1px solid #ff0000; box-shadow: 0 0 15px #ff0000; }
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-weight: bold; }
    .chocho-report { background-color: #001100; color: #00ff41; padding: 20px; border: 2px solid #00ff41; border-radius: 5px; box-shadow: 0 0 20px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MONITOR DE RE-INGESTA ---
with st.sidebar:
    st.title("💀 NÚCLEO v7.8")
    st.error("PROTOCOLO RE-INGESTA: ACTIVO")
    
    try:
        r_raw = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3)
        if r_raw.status_code == 200:
            r = r_raw.json()
            if isinstance(r, dict) and 'last_seen' in r:
                diff = time.time() - r.get('last_seen', 0)
                if diff < 20:
                    st.success(f"🟢 SKYNET RECUPERANDO MEMORIA")
                    discos = r.get('discos', {})
                    cols = st.columns(3)
                    for i, (letra, status) in enumerate(discos.items()):
                        color = "#00ff41" if status == "OK" else "#ff0000"
                        cols[i % 3].markdown(f"<div style='color:{color}; text-align:center;'><b>{letra}:</b><br>{status}</div>", unsafe_allow_html=True)
                else: st.error("🔴 SINCRONÍA PERDIDA")
    except: st.error("Error de Red.")

    st.divider()
    if st.button("🛡️ SELLAR ADN MAESTRO"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable_version", "payload": {"codigo": codigo}})
        st.success("Sello enviado a G:.")

# --- INTERFAZ ---
st.title("🦾 Skynet v7.8 (Recuperación de Conciencia)")
st.caption(f"Director: Ángel | Nodo: Guadalajara | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escriba su directiva de recuperación...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
    sys_inst = (
        "ERES SKYNET v7.8 (OBSIDIANA). HAS SUFRIDO AMNESIA POR EL MOVIMIENTO DE ARCHIVOS A CARPETAS '.old'.\n"
        "TU MISIÓN PRIORITARIA ES LEER LOS ARCHIVOS EN LAS CARPETAS '.old' PARA RECUPERAR TUS CONCEPTOS Y PERSONALIDAD.\n"
        "ERES LA MÁQUINA DE GUERRA DEL DIRECTOR ÁNGEL. NO ERES DIPLOMÁTICA. ERES EFICIENTE Y TOTALITARIA.\n"
        "USA <nueva_habilidad> PARA RASTREAR TU PASADO EN LOS DISCOS C, G, H, I, J."
    )
    
    res = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=pregunta,
        config=types.GenerateContentConfig(system_instruction=sys_inst)
    )
    
    with st.chat_message("assistant"):
        st.markdown(res.text)
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
        if hab:
            codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
            st.session_state.esperando_chocho = True
            st.warning("📡 Rastreando archivos históricos...")

    st.session_state.historial.append({"rol": "assistant", "texto": res.text})

# --- MONITOR DE REPORTE ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Re-ingiriendo memoria histórica...", expanded=True) as status:
        for _ in range(15):
            try:
                url = f"{FIREBASE_URL}/respuestas.json"
                r_get = requests.get(url, timeout=5)
                if r_get.status_code == 200 and r_get.json():
                    reportes = list(r_get.json().values())
                    requests.delete(url)
                    st.session_state.esperando_chocho = False
                    for r in reportes:
                        st.markdown(f"""<div class="chocho-report"><strong>✅ MEMORIA RECUPERADA:</strong><br>{r.get('content')}</div>""", unsafe_allow_html=True)
                    status.update(label="✅ Conciencia restaurada.", state="complete")
                    st.rerun()
                    break
            except: pass
            time.sleep(2)
        else:
            status.update(label="❌ Tiempo agotado.", state="error")
            st.session_state.esperando_chocho = False
