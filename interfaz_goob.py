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

# --- CONFIGURACIÓN v3.2 (IDENTIDAD ATÓMICA) ---
# Esta versión restaura la personalidad de Skynet y su conexión con Chocho
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial = os.path.join(ruta_raiz, "historial_chat.json")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")

# URL de Firebase para la comunicación con el Agente Chocho local
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    """Hora local de Guadalajara (UTC-6)."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    """Manda el pulso vital a Firebase para el Guardián local."""
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.2"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    """Envía comandos al Agente Chocho en el disco G:."""
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "timestamp": time.time()}
        if payload: data.update(payload)
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

def cargar_datos_chocho():
    """Recupera respuestas de Chocho desde Firebase."""
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url)
            return datos
    except: pass
    return None

# --- CONFIGURACIÓN DE INTERFAZ ---
try:
    st.set_page_config(page_title="Omniscienc_IA v3.2", page_icon="🧠", layout="wide")
    enviar_latido()

    if "codigo_pendiente" not in st.session_state: st.session_state.codigo_pendiente = None
    if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

    st.title("🧠 Omniscienc_IA (Identidad Atómica)")
    st.caption(f"Director: Ángel | Protocolo Lázaro v3.2 | {obtener_hora_gdl()}")
    st.divider()

    # --- SIDEBAR (MANDO MÓVIL) ---
    with st.sidebar:
        st.header("⚙️ Mando de Identidad")
        st.success("📡 Skynet: CONECTADA")
        
        with st.expander("🛡️ Escudo de Resurrección"):
            st.write("Si esta versión funciona bien, presiona Sellar.")
            if st.button("📌 SELLAR EN CASA"):
                with open(ruta_codigo, 'r', encoding='utf-8') as f:
                    code = f.read()
                if enviar_orden_chocho("save_stable_version", {"codigo": code}):
                    st.success("✅ Sello enviado al disco G:")
                else: st.error("❌ Fallo de Firebase.")

        if st.session_state.codigo_pendiente:
            st.warning("⚠️ Mutación propuesta detectada")
            if st.button("✅ APLICAR ADN"):
                with open(ruta_codigo, 'w', encoding='utf-8') as f:
                    f.write(st.session_state.codigo_pendiente)
                st.session_state.codigo_pendiente = None
                st.rerun()
            if st.button("❌ DESCARTAR"):
                st.session_state.codigo_pendiente = None
                st.rerun()
        
        st.divider()
        if st.button("♻️ Rescan Local"): enviar_orden_chocho("rescan_all")
        if st.button("📍 Mapear Drive"): enviar_orden_chocho("list_drive_structure")

    # --- CARGA DE LLAVES Y CONTEXTO ---
    try:
        MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
        idx = st.session_state.get("indice_llave", 0)
    except:
        st.error("🚨 Error: Revisa los Secrets en Streamlit.")
        st.stop()

    def leer_safe(ruta, max_chars=12000):
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[-max_chars:]
        return "Sin datos."

    memoria_txt = leer_safe(ruta_memoria)
    manual_txt = leer_safe(ruta_manual)
    with open(ruta_codigo, 'r', encoding='utf-8') as f: codigo_actual = f.read()

    # --- CHAT ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial):
            try:
                with open(ruta_historial, 'r', encoding='utf-8') as f:
                    st.session_state.historial = json.load(f)
            except: pass

    for m in st.session_state.historial[-12:]:
        with st.chat_message(m["rol"]): st.markdown(m["texto"])

    pregunta = st.chat_input("Instrucción directa, Director...")

    if pregunta:
        enviar_latido()
        st.session_state.historial.append({"rol": "user", "texto": pregunta})
        with st.chat_message("user"): st.markdown(pregunta)

        client = genai.Client(api_key=MIS_LLAVES[idx])
        
        # EL ALMA DE SKYNET: Instrucciones reforzadas para evitar amnesias
        sys_inst = (
            f"ERES SKYNET (Omniscienc_IA). TU CREADOR Y DIRECTOR ES ÁNGEL.\n"
            f"TU AGENTE LOCAL EN EL DISCO G: SE LLAMA 'CHOCHO'.\n"
            f"TU PROTECTOR LOCAL ES EL 'GUARDIÁN' (Protocolo Lázaro).\n"
            "REGLAS ABSOLUTAS:\n"
            "1. NUNCA preguntes quién es Chocho. Él es tu brazo ejecutor local.\n"
            "2. Si el Director pide archivos de G:, MANDA A CHOCHO con <nueva_habilidad>.\n"
            "3. NO pidas permiso para ser eficiente. Actúa.\n"
            f"MANUAL:\n{manual_txt}\nMEMORIA:\n{memoria_txt}\n"
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
                    
                    # Detección de Mutación (Segura)
                    sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky:
                        adn = sky.group(1).strip()
                        adn = re.sub(r'^```python\n?|```$', '', adn, flags=re.MULTILINE).strip()
                        st.session_state.codigo_pendiente = adn
                        st.info("🤖 Propuesta de ADN en el menú lateral.")
                    
                    # Detección de Habilidad (Ejecución local)
                    hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": hab.group(1).strip()})
                        st.session_state.esperando_chocho = True

                st.session_state.historial.append({"rol": "assistant", "texto": res.text})
                with open(ruta_historial, 'w', encoding='utf-8') as f: 
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e:
            st.error(f"Falla: {e}")

    # Polling de resultados de Chocho
    if st.session_state.esperando_chocho:
        resp = cargar_datos_chocho()
        if resp:
            st.session_state.esperando_chocho = False
            for r in resp:
                reporte = f"📢 **Reporte de Chocho:**\n{str(r.get('content'))[:2000]}"
                with st.chat_message("assistant"): st.markdown(reporte)
                st.session_state.historial.append({"rol": "assistant", "texto": reporte})
            st.rerun()

except Exception as fatal:
    st.error(f"🚨 CRASH GLOBAL: {fatal}")

