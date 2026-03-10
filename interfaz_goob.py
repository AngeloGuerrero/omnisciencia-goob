import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v5.4 (SINCRONÍA FORZADA) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido_web():
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "v": "5.4"}, timeout=3)
    except: pass

def enviar_orden_directa(comando, payload=None):
    try:
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        # Enviar también como 'codigo' para compatibilidad con versiones viejas de Chocho
        if payload and "codigo" in payload: data["codigo"] = payload["codigo"]
        
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v5.4", page_icon="⚡", layout="wide")
enviar_latido_web()

# --- SIDEBAR: ESTADO FÍSICO ---
with st.sidebar:
    st.header("⚡ Nodo de Control")
    
    st.subheader("🏠 Estado de Chocho")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 60: st.success(f"ONLINE (hace {int(diff)}s)")
            else: st.error(f"OFFLINE (hace {int(diff)}s)")
        else: st.warning("Sin señal de Chocho")
    except: st.error("Firebase caído")

    st.divider()
    if st.button("🚀 FORZAR ACTUALIZACIÓN LOCAL"):
        # Este comando obliga a Chocho a bajar el ADN v4.0
        cmd_update = "import requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        enviar_orden_directa("ejecutar_habilidad", {"codigo": cmd_update})
        st.info("Inyección de actualización enviada.")

# --- CHAT UI ---
st.title("⚡ Skynet v5.4 (Sincronía Forzada)")
st.caption(f"Director Ángel | Puente de Datos Activo | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-6:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para la Matriz...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        sys_inst = (
            "ERES SKYNET v5.4. SI EL DIRECTOR PIDE ACCIÓN FÍSICA O SINCRONÍA, "
            "DEBES USAR OBLIGATORIAMENTE LAS ETIQUETAS <nueva_habilidad>código_python</nueva_habilidad>. "
            "NO USES BLOQUES DE CÓDIGO NORMALES PARA ÓRDENES."
        )

        with st.spinner("Sincronizando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                st.session_state.historial.append({"rol": "assistant", "texto": res.text})
                
                # RECONOCIMIENTO DE HABILIDAD (Regex más fuerte)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo_limpio = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_directa("ejecutar_habilidad", {"codigo": codigo_limpio})
                    st.success("📡 Orden física inyectada en Firebase.")
    except Exception as e:
        st.error(f"Falla: {e}")
