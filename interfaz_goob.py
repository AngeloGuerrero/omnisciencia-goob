import streamlit as st
import google.generativeai as genai
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v8.1 (SINCRONÍA TOTAL) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

st.set_page_config(page_title="Omnisciencia v8.1", page_icon="🦾", layout="wide")

# --- UI ESTILO DARK ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stChatMessage"] { background-color: #161b22 !important; border: 1px solid #30363d; border-radius: 8px; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    .chocho-report { background-color: #000; color: #39ff14; padding: 10px; border-radius: 5px; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🦾 NÚCLEO v8.1")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r and (time.time() - r.get('last_seen', 0)) < 60:
            st.success(f"🟢 CHOCHO VIVO ({r.get('ts_human')})")
            mapa = r.get('mapa_goob', {})
            if mapa:
                with st.expander("📍 MAPA TERRITORIAL", expanded=True):
                    st.write("**Captación:**", ", ".join(mapa.get('captacion', [])))
        else:
            st.error("🔴 CHOCHO OFFLINE")
    except:
        st.warning("⚠️ Error Firebase")

# --- LÓGICA DE IA ---
def llamar_ia(instruccion, prompt):
    llaves = ["llave_1", "llave_2", "llave_3"]
    for alias in llaves:
        try:
            if alias in st.secrets["api_keys"]:
                genai.configure(api_key=st.secrets["api_keys"][alias])
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instruccion)
                res = model.generate_content(prompt)
                return res.text, alias
        except:
            continue
    return "❌ Error: Revisa tus llaves en Secrets.", "NINGUNA"

# --- INTERFAZ CHAT ---
st.title("Gestión Omnisciencia GOOB")
if "historial" not in st.session_state: st.session_state.historial = []

for m in st.session_state.historial[-6:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escriba su instrucción...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    # Contexto para la IA
    sys_inst = "ERES OMNISCIENCIA. DIRECTOR: ÁNGEL. Usa el mapa de G: para no inventar rutas."
    
    with st.spinner("Conectando..."):
        respuesta, llave = llamar_ia(sys_inst, pregunta)

    with st.chat_message("assistant"):
        st.markdown(respuesta)
        st.caption(f"📡 Vía: {llave}")
        # Detectar habilidad
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', respuesta, re.DOTALL)
        if hab:
            codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
            st.info("🛠️ Orden enviada a Chocho local.")

    st.session_state.historial.append({"rol": "assistant", "texto": respuesta})
