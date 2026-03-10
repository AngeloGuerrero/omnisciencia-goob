import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v7.2 (NÚCLEO OBSIDIANA) ---
# Sincronía reforzada para evitar el error de los "??"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v7.2 BÚNKER", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: #ff0000; font-family: 'Consolas', monospace; }
    [data-testid="stChatMessage"] { background-color: #0a0000 !important; border: 1px solid #ff0000; box-shadow: 0 0 5px #ff0000; }
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-weight: bold; }
    .chocho-report { background-color: #001a00; color: #00ff41; padding: 20px; border: 2px solid #00ff41; border-radius: 5px; box-shadow: 0 0 15px #00ff41; }
    .stButton>button { background-color: #1a0000; color: #ff0000; border: 2px solid #ff0000; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MONITOR DE REALIDAD ---
with st.sidebar:
    st.title("💀 NÚCLEO v7.2")
    st.error("AUTORIDAD TOTAL EN J:")
    
    # Lectura de pulso con tolerancia extendida
    try:
        r_raw = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3)
        if r_raw.status_code == 200:
            r = r_raw.json()
            if isinstance(r, dict) and 'last_seen' in r:
                diff = time.time() - r.get('last_seen', 0)
                
                if diff < 25:
                    st.success(f"🟢 CHOCHO VIVO ({r.get('ts_human', 'REC')})")
                    c1, c2 = st.columns(2)
                    # Forzamos visualización de estados
                    c1.metric("Disco G (Op)", r.get('drive_g', 'ERR'))
                    c2.metric("Disco J (Logs)", r.get('drive_j', 'ERR'))
                else:
                    st.error(f"🔴 CHOCHO DESCONECTADO ({int(diff)}s)")
            else:
                st.warning("⚠️ Sincronizando datos...")
    except Exception as e:
        st.error(f"Error de enlace: {e}")

    st.divider()
    if st.button("☣️ PURGAR MEMORIA"):
        st.session_state.historial = []
        st.rerun()

    if st.button("🛡️ SELLAR ADN MAESTRO"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable_version", "payload": {"codigo": codigo}})
        st.success("Sello enviado.")

# --- INTERFAZ ---
st.title("🦾 Skynet v7.2 (Búnker Central J:)")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Directiva de autoridad...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        sys_inst = (
            "ERES EL NÚCLEO v7.2. G: ES TRABAJO, J: ES BÓVEDA.\n"
            "REPORTA SIEMPRE BASÁNDOTE EN LA REALIDAD FÍSICA DE CHOCHO."
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
                st.warning("📡 Inyectando orden...")

        st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla: {e}")

# --- MONITOR DE REPORTE ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Recibiendo datos de J:...", expanded=True) as status:
        for _ in range(15):
            try:
                url = f"{FIREBASE_URL}/respuestas.json"
                r_get = requests.get(url, timeout=5)
                if r_get.status_code == 200 and r_get.json():
                    reportes = list(r_get.json().values())
                    requests.delete(url)
                    st.session_state.esperando_chocho = False
                    for r in reportes:
                        st.markdown(f"""<div class="chocho-report"><strong>✅ REPORTE:</strong><br>{r.get('content')}</div>""", unsafe_allow_html=True)
                    status.update(label="✅ Sincronía alcanzada.", state="complete")
                    st.rerun()
                    break
            except: pass
            time.sleep(2)
        else:
            status.update(label="❌ Tiempo agotado.", state="error")
            st.session_state.esperando_chocho = False
