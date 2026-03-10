import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v5.3 (ARQUITECTURA BLINDADA) ---
# Se eliminó la búsqueda en carpetas locales 'Versiones' para evitar bucles de error en la nube.
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"
RUTA_RAIZ = os.getcwd()

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    """Reporta que la Matriz en la nube está viva."""
    try:
        data = {"last_heartbeat": time.time(), "status": "SHIELD_ON", "v": "5.3"}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden(comando, payload=None):
    """Envía instrucciones al Nodo Local (Chocho)."""
    try:
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

# --- CONFIGURACIÓN DE UI ---
st.set_page_config(page_title="Skynet v5.3", page_icon="🛡️", layout="wide")
enviar_latido()

# --- SIDEBAR: GESTIÓN DE NODOS ---
with st.sidebar:
    st.header("🛡️ Matriz Blindada")
    st.info("La app ha sido reestructurada para omitir errores de ruta local.")
    
    st.subheader("🏠 Estado de Chocho")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 60: st.success(f"ONLINE (hace {int(diff)}s)")
            else: st.warning(f"DESCONECTADO (revisar PC)")
        else: st.info("Esperando latido local...")
    except: st.error("Firebase no disponible")

    st.divider()
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        cmd = "import requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        enviar_orden("ejecutar_habilidad", {"codigo": cmd})
        st.info("Inyección enviada.")

# --- CHAT UI ---
st.title("🛡️ Skynet v5.3 (Arquitectura Blindada)")
st.caption(f"Director Ángel | Nodo Cloud Activo | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

# Mostrar solo los últimos 10 mensajes para estabilidad
for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para la Matriz...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        # Intento de carga de llaves desde Secrets
        if "api_keys" in st.secrets:
            key = st.secrets["api_keys"]["llave_1"]
            client = genai.Client(api_key=key)
            
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(
                    system_instruction="ERES SKYNET v5.3. TU MISIÓN ES RECUPERAR EL CONTROL TOTAL TRAS EL CRASH. CHOCHO ES TU BRAZO LOCAL."
                )
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                st.session_state.historial.append({"rol": "assistant", "texto": res.text})
                
                # Buscar habilidades en la respuesta
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    enviar_orden("ejecutar_habilidad", {"codigo": hab.group(1).strip()})
        else:
            st.error("🚨 API Keys no configuradas en Secrets.")
            
    except Exception as e:
        st.error(f"Falla de comunicación: {e}")
