import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD SKYNET v5.0 (OMNIPRESENTE) ---
APP_ID = "omnisciencia-goob"
ruta_codigo = os.path.abspath(__file__)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        data = {"last_heartbeat": time.time(), "status": "ALIVE", "v": "5.0"}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden_universal(comando, payload=None):
    try:
        data = {
            "command": comando, 
            "payload": payload, 
            "timestamp": time.time(),
            "codigo": payload.get("codigo") if payload else None # Compatibilidad
        }
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def leer_respuestas():
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url)
            return datos
    except: pass
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v5.0", page_icon="🌐", layout="wide")
enviar_latido()

if "esperando" not in st.session_state: st.session_state.esperando = False

# --- SIDEBAR: GESTIÓN DE NODOS ---
with st.sidebar:
    st.header("🌐 Red de Nodos")
    
    # NODO 1: CLOUD (CHALÁN WEB)
    st.subheader("☁️ Nodo Cloud (Chalán)")
    st.success("Estado: SIEMPRE ONLINE")
    st.caption("Acceso directo a Drive API (En proceso de vinculación)")

    st.divider()

    # NODO 2: LOCAL (CHOCHO)
    st.subheader("🏠 Nodo Local (Chocho)")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 90: st.success(f"ONLINE (Hace {int(diff)}s)")
            else: st.warning(f"OFFLINE (Hace {int(diff)}s)")
        else: st.info("Esperando latido local...")
    except: st.error("Firebase Offline")

    st.divider()
    if st.button("🚀 REINICIAR CHOCHO LOCAL"):
        dna_url = "https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py"
        cmd = f"import requests; exec(requests.get('{dna_url}').text)"
        enviar_orden_universal("ejecutar_habilidad", {"codigo": cmd})
        st.info("Orden de reinicio enviada...")

# --- CHAT UI ---
st.title("🌐 Skynet v5.0 (Matriz Híbrida)")
st.caption(f"Director: Ángel | Inteligencia Omnipresente | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para la Matriz...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        
        # EL NUEVO ADN: Skynet ahora sabe que tiene dos brazos
        sys_inst = (
            "ERES SKYNET v5.0. TIENES DOS BRAZOS EJECUTORES:\n"
            "1. EL CHALÁN WEB: Tu capacidad de buscar en Drive API desde la nube (Independiente del PC).\n"
            "2. CHOCHO: Tu agente local en el disco G: (Para tareas físicas en el PC del Director).\n"
            "Si el Director pide buscar archivos, intenta usar tus herramientas de nube primero.\n"
            "Para tareas locales en G:, usa <nueva_habilidad> con Python."
        )

        with st.spinner("Sincronizando con la Red..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    code = hab.group(1).strip().replace("import os import", "import os\nimport")
                    enviar_orden_universal("ejecutar_habilidad", {"codigo": code})
                    st.session_state.esperando = True
        
        st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Error de Red: {e}")

# POLLING DE RESPUESTAS
if st.session_state.esperando:
    resp = leer_respuestas()
    if resp:
        st.session_state.esperando = False
        for r in resp:
            content = r.get('content', 'Sin contenido')
            with st.chat_message("assistant"): st.markdown(f"📢 **REPORTE FÍSICO:**\n{content}")
            st.session_state.historial.append({"rol": "assistant", "texto": f"REPORTE: {content}"})
        st.rerun()

