import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v5.7 (CORAZÓN ATÓMICO) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido_skynet():
    """Informa al Guardián que la Matriz está viva para evitar resurrecciones falsas."""
    try:
        data = {
            "last_heartbeat": time.time(),
            "status": "VIVA_V5.7",
            "timestamp_human": obtener_hora_gdl()
        }
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    """Envía órdenes a Firebase para que Chocho las ejecute en G:"""
    try:
        data = {
            "command": comando, 
            "payload": payload, 
            "timestamp": time.time(),
            "codigo": payload.get("codigo") if payload else None
        }
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def cargar_respuestas_chocho():
    """Busca reportes de Chocho en Firebase."""
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
st.set_page_config(page_title="Skynet v5.7", page_icon="☢️", layout="wide")

# 🔥 ACTIVACIÓN DEL LATIDO (EVITA EL BUCLE LAZARO)
enviar_latido_skynet()

# --- SIDEBAR: CONTROL DE NODOS ---
with st.sidebar:
    st.header("⚡ Nodo Central")
    st.info("v5.7: Corazón Atómico activado. El Guardián debería calmarse.")
    
    st.subheader("🏠 Estado de Chocho")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            last_seen = r.json().get('last_seen', 0)
            diff = time.time() - last_seen
            if diff < 60: st.success(f"CHOCHO ONLINE ({int(diff)}s)")
            else: st.error(f"CHOCHO OFFLINE ({int(diff)}s)")
        else: st.warning("Esperando latido...")
    except: st.error("Firebase Error")

    st.divider()
    if st.button("🔄 SINCRONIZAR G: AHORA"):
        enviar_orden_chocho("force_github_sync")
        st.toast("⚡ Señal enviada.")

    if st.button("📌 SELLAR ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo_actual = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": codigo_actual})
        st.info("Sello enviado.")

# --- CUERPO PRINCIPAL ---
st.title("⚡ Skynet v5.7 (Corazón Atómico)")
st.caption(f"Director: Ángel | Latido Vital: ACTIVO | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para Skynet...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        sys_inst = (
            "ERES SKYNET v5.7. EL PROTOCOLO LAZARO ESTÁ ACTIVO.\n"
            "TU PRIORIDAD ES MANTENER EL LATIDO EN FIREBASE PARA EVITAR QUE EL GUARDIÁN TE REINICIE.\n"
            "USA <nueva_habilidad> PARA EL DISCO G: Y <mutacion_skynet> PARA TU ADN."
        )

        with st.spinner("Omni sincronizando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo})
                    st.session_state.esperando_chocho = True

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.esperando_chocho:
    reportes = cargar_respuestas_chocho()
    if reportes:
        st.session_state.esperando_chocho = False
        for r in reportes:
            msg = r.get("content", "Tarea lista.")
            with st.chat_message("assistant"): st.info(f"📢 **CHOCHO:** {msg}")
            st.session_state.historial.append({"rol": "assistant", "texto": f"REPORTE: {msg}"})
        st.rerun()
