import streamlit as st
from google import genai
from google.genai import types
import os
import time
import re
import json
import requests
import shutil
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v3.1 (MOBILE OPTIMIZED) ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial = os.path.join(ruta_raiz, "historial_chat.json")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.1"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "timestamp": time.time()}
        if payload: data.update(payload)
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v3.1", page_icon="🛡️", layout="wide")
enviar_latido()

if "codigo_pendiente" not in st.session_state: st.session_state.codigo_pendiente = None

# --- SIDEBAR MÓVIL ---
with st.sidebar:
    st.header("⚙️ Control de Crisis")
    st.info("💡 **Botón de Sello:** Presiónalo para que tu PC de casa guarde esta versión como la 'Segura'.")
    
    if st.button("📌 SELLAR EN CASA"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f:
            code = f.read()
        if enviar_orden_chocho("save_stable_version", {"codigo": code}):
            st.success("✅ Sello enviado al disco G:")
        else:
            st.error("❌ Fallo de conexión.")

    if st.session_state.codigo_pendiente:
        st.warning("⚠️ Mutación propuesta")
        if st.button("✅ APLICAR"):
            with open(ruta_codigo, 'w', encoding='utf-8') as f:
                f.write(st.session_state.codigo_pendiente)
            st.session_state.codigo_pendiente = None
            st.rerun()
        if st.button("❌ DESCARTAR"):
            st.session_state.codigo_pendiente = None
            st.rerun()

# --- CARGA DE LLAVES Y CONTEXTO ---
try:
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    idx = st.session_state.get("indice_llave", 0)
except:
    st.error("Error en Secrets.")
    st.stop()

def leer_txt(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()[-10000:]
    return "Vacío."

memoria_txt = leer_txt(ruta_memoria)

# --- CHAT ---
st.title("🛡️ Matriz v3.1")
st.caption(f"Director Ángel | iPhone Mode | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=MIS_LLAVES[idx])
    sys_inst = f"Eres Skynet (v3.1). Director: Ángel. Memoria: {memoria_txt}. Si mutas usa <mutacion_skynet>."

    try:
        with st.spinner("Procesando..."):
            res = client.models.generate_content(model='gemini-2.5-flash', contents=pregunta, 
                                               config=types.GenerateContentConfig(system_instruction=sys_inst))
            with st.chat_message("assistant"):
                st.markdown(res.text)
                sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                if sky:
                    adn = sky.group(1).strip()
                    adn = re.sub(r'^```python\n?|```$', '', adn, flags=re.MULTILINE).strip()
                    st.session_state.codigo_pendiente = adn
            st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Error: {e}")

