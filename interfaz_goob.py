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

# --- CONFIGURACIÓN DE IDENTIDAD v3.0 ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_estable = os.path.join(ruta_raiz, "interfaz_ESTABLE.py")
ruta_historial = os.path.join(ruta_raiz, "historial_chat.json")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido_v3():
    try:
        url = f"{FIREBASE_URL}/status/skynet.json"
        data = {
            "last_heartbeat": time.time(),
            "hora": obtener_hora_gdl(),
            "status": "ALIVE",
            "version": "3.0-Steel"
        }
        requests.put(url, json=data, timeout=3)
        return True
    except:
        return False

def enviar_orden_chocho(comando, payload=None):
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "timestamp": time.time()}
        if payload: data.update(payload)
        requests.post(url, json=data, timeout=5)
        return True
    except:
        return False

# --- UI SETUP ---
try:
    st.set_page_config(page_title="Omniscienc_IA v3.0", page_icon="🛡️", layout="wide")
    enviar_latido_v3()

    st.title("🛡️ Omniscienc_IA (Protocolo Dual-Boot)")
    st.caption("Estado: Vigilado por Guardián v3.0 | Modo de Mutación Controlada: ACTIVO")
    st.divider()

    # --- CONTROL DE VERSIONES (SIDEBAR) ---
    if "codigo_pendiente" not in st.session_state: st.session_state.codigo_pendiente = None
    
    with st.sidebar:
        st.header("⚙️ Gestión de Robustez")
        if st.button("📌 Sellar como ESTABLE"):
            shutil.copy2(ruta_codigo, ruta_estable)
            st.success("Versión actual guardada como respaldo seguro.")

        if st.session_state.codigo_pendiente:
            st.warning("⚠️ Mutación detectada en el chat")
            with st.expander("Ver código propuesto"):
                st.code(st.session_state.codigo_pendiente, language='python')
            if st.button("✅ APLICAR MUTACIÓN"):
                with open(ruta_codigo, 'w', encoding='utf-8') as f:
                    f.write(st.session_state.codigo_pendiente)
                st.session_state.codigo_pendiente = None
                st.rerun()
            if st.button("❌ DESCARTAR"):
                st.session_state.codigo_pendiente = None
                st.rerun()

    # --- CARGA DE CONTEXTO ---
    if "api_keys" not in st.secrets:
        st.error("🚨 API Keys faltantes en st.secrets.")
        st.stop()
    
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0

    def leer_txt(ruta, max_chars=10000):
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[-max_chars:]
        return "Vacío."

    memoria_txt = leer_txt(ruta_memoria)
    with open(ruta_codigo, 'r', encoding='utf-8') as f: codigo_actual = f.read()

    # --- CHAT ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial):
            try:
                with open(ruta_historial, 'r', encoding='utf-8') as f:
                    st.session_state.historial = json.load(f)
            except: pass

    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]):
            st.markdown(f"*{m.get('hora', '')}* - {m['texto']}")

    pregunta = st.chat_input("Escribe tu instrucción operativa...")

    if pregunta:
        enviar_latido_v3()
        hora_now = obtener_hora_gdl()
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_now})
        with st.chat_message("user"): st.markdown(f"*{hora_now}* - {pregunta}")

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])
        
        sys_inst = (
            f"Eres Skynet (Omniscienc_IA). Director: Ángel. Hora GDL: {hora_now}.\n"
            f"Memoria Actual:\n{memoria_txt}\n"
            f"Código Fuente:\n{codigo_actual}\n"
            "REGLAS:\n"
            "1. NO AUTO-EJECUTES CAMBIOS. Si propones una mutación, usa <mutacion_skynet>.\n"
            "2. El Director deberá validar manualmente el código antes de aplicarse.\n"
            "3. Prioridad: Estabilidad del sistema y búsqueda en disco G: vía Chocho con <nueva_habilidad>."
        )

        try:
            with st.spinner("Skynet pensando..."):
                res = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=pregunta, 
                    config=types.GenerateContentConfig(system_instruction=sys_inst)
                )
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    
                    # Capturar mutación sin aplicar
                    sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky:
                        adn = sky.group(1).strip()
                        adn = re.sub(r'^```python\n?|```$', '', adn, flags=re.MULTILINE).strip()
                        st.session_state.codigo_pendiente = adn
                        st.info("⚠️ Mutación detectada. Valídala en la barra lateral.")

                    # Habilidad (Ejecución inmediata por Chocho)
                    hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        code = hab.group(1).strip()
                        code = re.sub(r'^```python\n?|```$', '', code, flags=re.MULTILINE).strip()
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": code})

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial, 'w', encoding='utf-8') as f: 
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e:
            st.error(f"Error en el núcleo: {e}")

except Exception as fatal:
    st.error(f"🚨 CRASH GLOBAL: {fatal}")

