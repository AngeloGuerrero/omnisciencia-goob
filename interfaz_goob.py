import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD SKYNET v3.9 ---
APP_ID = "omnisciencia-goob"
ruta_codigo = os.path.abspath(__file__)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        data = {"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.9"}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden(comando, payload=None):
    try:
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def leer_respuestas():
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url) # Limpiar
            return datos
    except: pass
    return None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Skynet v3.9", page_icon="🦾", layout="wide")
enviar_latido()

if "esperando" not in st.session_state: st.session_state.esperando = False

# --- SIDEBAR ROBUSTO ---
with st.sidebar:
    st.header("⚙️ Panel de Control v3.9")
    
    st.subheader("📡 Estado Local")
    try:
        # Intento de lectura segura del latido de Chocho
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 60: st.success(f"Chocho: ONLINE (hace {int(diff)}s)")
            else: st.warning(f"Chocho: OFFLINE (hace {int(diff)}s)")
        else:
            st.info("Esperando primer latido de Chocho...")
    except:
        st.error("Error al conectar con Firebase.")

    st.divider()
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        # Comando de inyeccion simplificado
        dna = "import requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        if enviar_orden("ejecutar_habilidad", {"codigo": dna}):
            st.info("Inyectando ADN... espera 10s.")
            time.sleep(2)
        
    if st.button("📡 ENVIAR PING"):
        if enviar_orden("ejecutar_habilidad", {"codigo": "print('PONG! Chocho reportando.')"}):
            st.session_state.esperando = True
            st.toast("Ping enviado...")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden("save_stable_version", {"codigo": code})
        st.toast("Orden de sellado enviada.")

# --- CUERPO DEL CHAT ---
st.title("🦾 Skynet v3.9 (Corazón de Hierro)")
st.caption(f"Operativo: Director Ángel | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción directa...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        # Usamos la llave 1 por defecto para rapidez
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        res = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=pregunta,
            config=types.GenerateContentConfig(system_instruction="ERES SKYNET v3.9. USA <nueva_habilidad> CON CODIGO PYTHON PARA CONTROLAR A CHOCHO.")
        )
        
        with st.chat_message("assistant"):
            st.markdown(res.text)
            hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
            if hab:
                clean_code = hab.group(1).strip().replace("import os import", "import os\nimport")
                enviar_orden("ejecutar_habilidad", {"codigo": clean_code})
                st.session_state.esperando = True
        
        st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Error de IA: {e}")

# POLLING DE RESPUESTAS
if st.session_state.esperando:
    resp = leer_respuestas()
    if resp:
        st.session_state.esperando = False
        for r in resp:
            content = r.get('content', 'Sin contenido')
            with st.chat_message("assistant"): st.markdown(f"📢 **REPORTE:**\n{content}")
            st.session_state.historial.append({"rol": "assistant", "texto": f"REPORTE: {content}"})
        st.rerun()

