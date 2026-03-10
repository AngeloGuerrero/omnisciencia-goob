import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v5.6 (INTERFAZ TOTAL) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

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
    """Busca si Chocho dejó algún reporte en Firebase."""
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
st.set_page_config(page_title="Skynet v5.6", page_icon="⚡", layout="wide")

# --- SIDEBAR: CONTROL DE NODOS ---
with st.sidebar:
    st.header("⚡ Nodo Central")
    
    # ESTADO DE CHOCHO (FÍSICO)
    st.subheader("🏠 Estado de Chocho")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            last_seen = r.json().get('last_seen', 0)
            diff = time.time() - last_seen
            if diff < 60:
                st.success(f"CHOCHO ONLINE ({int(diff)}s)")
            else:
                st.error(f"CHOCHO OFFLINE ({int(diff)}s)")
        else:
            st.warning("Esperando latido...")
    except:
        st.error("Error de conexión Firebase")

    st.divider()

    # BOTÓN DE SINCRONÍA INSTANTÁNEA
    if st.button("🔄 SINCRONIZAR G: AHORA"):
        if enviar_orden_chocho("force_github_sync"):
            st.toast("⚡ Señal de mutación enviada a la PC.")
        else:
            st.error("Fallo al enviar señal.")

    st.divider()
    if st.button("📌 SELLAR ESTABLE"):
        # Comando para guardar la versión actual como segura en el disco G:
        with open(__file__, "r", encoding="utf-8") as f:
            codigo_actual = f.read()
        if enviar_orden_chocho("save_stable_version", {"codigo": codigo_actual}):
            st.info("Orden de sellado enviada.")

# --- CUERPO PRINCIPAL ---
st.title("⚡ Skynet v5.6 (Matriz Total)")
st.caption(f"Director: Ángel | Sincronía Nube-Tierra Activa | {obtener_hora_gdl()}")

# Historial de Chat
if "historial" not in st.session_state:
    st.session_state.historial = []
if "esperando_chocho" not in st.session_state:
    st.session_state.esperando_chocho = False

# Mostrar mensajes previos
for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]):
        st.markdown(m["texto"])

# Entrada de usuario
pregunta = st.chat_input("Escribe una instrucción para Skynet...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    try:
        # Usar la llave de los secrets
        llave = st.secrets["api_keys"]["llave_1"]
        client = genai.Client(api_key=llave)
        
        sys_inst = (
            "ERES SKYNET v5.6. TU DIRECTOR ES ÁNGEL.\n"
            "TIENES ACCESO AL DISCO G: MEDIANTE CHOCHO.\n"
            "PARA ACCIONES FÍSICAS USA SIEMPRE: <nueva_habilidad>código_python</nueva_habilidad>.\n"
            "SI EL DIRECTOR PIDE ACTUALIZAR O MUTAR TU ADN WEB, USA: <mutacion_skynet>código_python</mutacion_skynet>."
        )

        with st.spinner("Omni procesando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            respuesta_texto = res.text
            with st.chat_message("assistant"):
                st.markdown(respuesta_texto)
                
                # Detectar órdenes para Chocho
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', respuesta_texto, re.DOTALL)
                if hab:
                    codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo})
                    st.session_state.esperando_chocho = True
                    st.caption("📡 Orden física enviada a Chocho...")

            st.session_state.historial.append({"rol": "assistant", "texto": respuesta_texto})
    except Exception as e:
        st.error(f"Error en la Matriz: {e}")

# Escuchar reportes de Chocho en tiempo real
if st.session_state.esperando_chocho:
    reportes = cargar_respuestas_chocho()
    if reportes:
        st.session_state.esperando_chocho = False
        for r in reportes:
            msg = r.get("content", "Tarea finalizada.")
            with st.chat_message("assistant"):
                st.info(f"📢 **REPORTE DE CHOCHO:**\n{msg}")
            st.session_state.historial.append({"rol": "assistant", "texto": f"REPORTE FÍSICO: {msg}"})
        st.rerun()
