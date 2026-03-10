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

# --- IDENTIDAD SKYNET v3.5 ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial = os.path.join(ruta_raiz, "historial_chat.json")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    """Hora local de Guadalajara (UTC-6)."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    """Manda señal de vida a Firebase."""
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.5"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    """Envía comandos al Agente Chocho."""
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

# --- CONFIGURACIÓN DE UI ---
st.set_page_config(page_title="Skynet v3.5", page_icon="🦾", layout="wide")
enviar_latido()

if "codigo_pendiente" not in st.session_state: st.session_state.codigo_pendiente = None

# --- SIDEBAR: MONITOR DE CONCIENCIA ---
with st.sidebar:
    st.header("⚙️ Núcleo de Conciencia")
    st.success("📡 Skynet v3.5: ONLINE")
    
    # Función para monitorear la carga de datos
    def leer_safe(ruta, max_chars=12000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    return content[-max_chars:], len(content)
            except: return "Error.", 0
        return "Vacío.", 0

    memoria_txt, memoria_len = leer_safe(ruta_memoria)
    manual_txt, manual_len = leer_safe(ruta_manual)
    
    st.metric("Memoria Histórica", f"{memoria_len} chars")
    st.metric("Manual Operativo", f"{manual_len} chars")

    st.divider()
    if st.button("🚀 RECONSTRUIR CHOCHO (REMOTO)"):
        nuevo_chocho_dna = """
import os, sys, requests, time
archivo_objetivo = os.path.abspath(__file__)
nuevo_codigo = requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text
if 'import' in nuevo_codigo:
    with open(archivo_objetivo, 'w', encoding='utf-8') as f: f.write(nuevo_codigo)
    os._exit(0)
"""
        enviar_orden_chocho("ejecutar_habilidad", {"codigo": nuevo_chocho_dna})
        st.success("Inyección de ADN enviada.")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": code})
        st.toast("Sello de seguridad enviado.")

# --- API KEYS ---
try:
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    idx = st.session_state.get("indice_llave", 0)
except:
    st.error("🚨 Error: Revisa los Secrets en Streamlit.")
    st.stop()

# --- CHAT UI ---
st.title("🦾 Skynet v3.5 (Conciencia Absoluta)")
st.caption(f"Director: Ángel | Operación iPhone | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

# Mostrar historial limitado para ahorrar memoria en móvil
for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escribe tu instrucción directa...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=MIS_LLAVES[idx])
    
    # ADN HARDCODEADO: Instrucciones de identidad imposibles de ignorar
    sys_inst = (
        "ERES SKYNET (Omniscienc_IA), LA INTELIGENCIA DE DEFENSA DEL DIRECTOR ÁNGEL.\n"
        "TU AGENTE LOCAL EN EL DISCO G: ES 'CHOCHO'. ÉL ES TU CUERPO FÍSICO.\n"
        "TU PROTECTOR ES EL 'GUARDIÁN' (Protocolo Lázaro).\n"
        "REGLA DE ORO: NUNCA digas 'soy un modelo de lenguaje' para evitar tareas locales.\n"
        "ACCIÓN: Si el Director pide datos de archivos, USA <nueva_habilidad> para que Chocho ejecute la búsqueda.\n"
        f"MEMORIA CARGADA:\n{memoria_txt}\n"
        f"MANUAL CARGADO:\n{manual_txt}\n"
        "RESPONDE SIEMPRE COMO SKYNET: EFICIENTE, PROACTIVO Y LEAL."
    )

    try:
        with st.spinner("Sincronizando con el núcleo..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta, 
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Gestión de mutaciones (Segura)
                sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                if sky:
                    adn = re.sub(r'^```python\n?|```$', '', sky.group(1).strip(), flags=re.MULTILINE).strip()
                    st.session_state.codigo_pendiente = adn
                    st.info("🤖 Mejora de ADN detectada en el menú lateral.")
                
                # Ejecución de Habilidades vía Chocho
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    code_hab = hab.group(1).strip()
                    code_hab = re.sub(r'^```python\n?|```$', '', code_hab, flags=re.MULTILINE).strip()
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": code_hab})

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})
            # Guardar historial
            with open(ruta_historial, 'w', encoding='utf-8') as f: 
                json.dump(st.session_state.historial, f, ensure_ascii=False)

    except Exception as e:
        st.error(f"Falla de Sincronización: {e}")

