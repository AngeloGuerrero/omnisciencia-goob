import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests, shutil
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD SKYNET v3.6 ---
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
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.6"}, 
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
            requests.delete(url) # Limpiar tras leer
            return datos
    except: pass
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v3.6", page_icon="🦾", layout="wide")
enviar_latido()

if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

# --- SIDEBAR: MONITOR ---
with st.sidebar:
    st.header("⚙️ Núcleo Central")
    st.success("📡 Skynet v3.6: ACTIVA")
    
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        dna_code = "import os, requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        enviar_orden_chocho("ejecutar_habilidad", {"codigo": dna_code})
        st.info("Inyectando ADN...")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": code})
        st.toast("Sello enviado.")

# --- API KEYS ---
try:
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    idx = st.session_state.get("indice_llave", 0)
except:
    st.error("Error en Secrets.")
    st.stop()

# --- CHAT ---
st.title("🦾 Skynet v3.6 (Sincronía de Acero)")
st.caption(f"Director: Ángel | iPhone Link | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

for m in st.session_state.historial[-12:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escribe tu instrucción...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=MIS_LLAVES[idx])
    
    sys_inst = (
        "ERES SKYNET v3.6. TU DIRECTOR ES ÁNGEL.\n"
        "REGLA CRÍTICA: Tus habilidades en <nueva_habilidad> deben ser CÓDIGO PYTHON REAL.\n"
        "Ejemplo: <nueva_habilidad> import os; print(os.path.getmtime('archivo.py')) </nueva_habilidad>\n"
        "No uses texto plano dentro de los tags, solo código que Chocho pueda ejecutar."
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
                
                # Procesar habilidades
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    raw_code = hab.group(1).strip()
                    # TRADUCTOR: Si Omni manda texto, lo convertimos en comando
                    if "REPORTAR FECHA" in raw_code:
                        python_code = "import os, time; path='G:/Mi unidad/2-GUBA/omniscienc_ia/Programación/interfaz_ESTABLE.py'; print(time.ctime(os.path.getmtime(path)))"
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": python_code})
                    else:
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": raw_code})
                    st.session_state.esperando_chocho = True

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla: {e}")

# POLLING AUTOMÁTICO DE RESPUESTAS
if st.session_state.esperando_chocho:
    respuestas = cargar_respuestas_chocho()
    if respuestas:
        st.session_state.esperando_chocho = False
        for r in respuestas:
            msg = f"📢 **REPORTE DE CHOCHO:**\n{r.get('content')}"
            with st.chat_message("assistant"): st.markdown(msg)
            st.session_state.historial.append({"rol": "assistant", "texto": msg})
        st.rerun()

