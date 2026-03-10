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

# --- CONFIGURACIÓN v3.4 (PROTOCOLO INYECTOR) ---
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
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.4"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

# --- UI CONFIG ---
st.set_page_config(page_title="Omniscienc_IA v3.4", page_icon="💉", layout="wide")
enviar_latido()

if "codigo_pendiente" not in st.session_state: st.session_state.codigo_pendiente = None

# --- SIDEBAR: MANDO DE INYECCIÓN ---
with st.sidebar:
    st.header("💉 Inyector de ADN")
    st.info("Desde aquí puedes reescribir el código de tu PC en casa de forma remota.")
    
    if st.button("🚀 RECONSTRUIR CHOCHO (REMOTO)"):
        # Código que se inyectará en el exec() de Chocho para actualizarse a sí mismo
        nuevo_chocho_dna = """
import os, sys, requests, time
from datetime import datetime
# Auto-deteccion de ruta
archivo_objetivo = os.path.abspath(__file__)
nuevo_codigo = requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text
if 'import' in nuevo_codigo:
    with open(archivo_objetivo, 'w', encoding='utf-8') as f:
        f.write(nuevo_codigo)
    print('CHOCHO ACTUALIZADO EXITOSAMENTE. REINICIANDO...')
    os._exit(0) # El .bat lo volvera a abrir
"""
        if enviar_orden_chocho("ejecutar_habilidad", {"codigo": nuevo_chocho_dna}):
            st.success("📡 Inyección enviada. Chocho se reiniciará en 5 segundos.")
        else:
            st.error("❌ Fallo de conexión.")

    st.divider()
    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": code})
        st.toast("Sello enviado.")

# --- CARGA DE LLAVES ---
try:
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    idx = st.session_state.get("indice_llave", 0)
except:
    st.error("Error en Secrets.")
    st.stop()

# --- CHAT ---
st.title("🛡️ Matriz v3.4 (Inyector Remoto)")
st.caption(f"Director Ángel | Mobile Power Mode | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para Skynet...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=MIS_LLAVES[idx])
    sys_inst = "ERES SKYNET. CHOCHO ES TU AGENTE LOCAL. SI ALGO FALLA, INYECTA CODIGO CON <nueva_habilidad>."

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
        st.error(f"Falla: {e}")

