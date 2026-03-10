import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD SKYNET v3.8 ---
APP_ID = "omnisciencia-goob"
ruta_codigo = os.path.abspath(__file__)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.8"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

def cargar_respuestas_chocho():
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
st.set_page_config(page_title="Skynet v3.8", page_icon="🦾", layout="wide")
enviar_latido()

if "esperando" not in st.session_state: st.session_state.esperando = False

# --- SIDEBAR: DIAGNÓSTICO ---
with st.sidebar:
    st.header("⚙️ Panel de Control v3.8")
    
    # Verificar si Chocho local está vivo (Heartbeat de Chocho)
    try:
        st.subheader("📡 Estado Local")
        beat_res = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if beat_res:
            diff = time.time() - beat_res.get('last_seen', 0)
            if diff < 60: st.success(f"Chocho: ONLINE (hace {int(diff)}s)")
            else: st.warning(f"Chocho: DESCONECTADO (hace {int(diff)}s)")
    except: st.error("No se pudo leer estado de Chocho")

    st.divider()
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        # Forzamos una inyección que además reporte éxito
        dna_cmd = "import requests, os; c = requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text; exec(c)"
        enviar_orden_chocho("ejecutar_habilidad", {"codigo": dna_cmd})
        st.info("Inyectando nuevo ADN...")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": code})
        st.toast("Sello enviado.")

# --- CHAT ---
st.title("🦾 Skynet v3.8 (Diagnóstico)")
st.caption(f"Director: Ángel | Enlace Directo | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para el sistema...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
    
    sys_inst = (
        "ERES SKYNET v3.8. TU DIRECTOR ES ÁNGEL.\n"
        "REGLA DE CÓDIGO: Cada instrucción 'import' debe ir en su propia línea.\n"
        "Ejemplo correcto:\nimport os\nimport time\n"
        "Usa <nueva_habilidad> para enviar código Python puro."
    )

    try:
        with st.spinner("Omni operando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta, 
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    # Limpieza automática de errores de la IA
                    clean_code = hab.group(1).strip().replace("import os import", "import os\nimport")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": clean_code})
                    st.session_state.esperando = True

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Falla: {e}")

# POLLING DE RESPUESTAS
if st.session_state.esperando:
    with st.status("🔍 Chocho está procesando en el disco G:...", expanded=True) as status:
        for _ in range(20):
            resp = cargar_respuestas_chocho()
            if resp:
                st.session_state.esperando = False
                for r in resp:
                    msg = f"📢 **REPORTE FÍSICO:**\n{r.get('content')}"
                    with st.chat_message("assistant"): st.markdown(msg)
                    st.session_state.historial.append({"rol": "assistant", "texto": msg})
                status.update(label="✅ Respuesta recibida", state="complete")
                st.rerun()
                break
            time.sleep(2)
        else:
            status.update(label="❌ Chocho no respondió a tiempo", state="error")
            st.session_state.esperando = False

