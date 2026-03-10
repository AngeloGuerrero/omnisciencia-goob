import streamlit as st
from google import genai
from google.genai import types
import os
import time
import re
import json
import requests
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD DE ALTA DISPONIBILIDAD v2.4 ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")

# URL DIRECTA DE FIREBASE
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    """Hora exacta de Guadalajara (UTC-6)."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido_atomico():
    """Envía el pulso vital con máxima prioridad."""
    try:
        url = f"{FIREBASE_URL}/status/skynet.json"
        ts = time.time()
        data = {
            "last_heartbeat": ts, 
            "hora": obtener_hora_gdl(), 
            "status": "ALIVE",
            "msg": "Skynet v2.4 Reportando"
        }
        # Timeout corto para no trabar la UI, pero envío forzado
        requests.put(url, json=data, timeout=2)
        return True
    except:
        return False

def enviar_orden_chocho(comando, payload=None):
    """Protocolo de comunicación con el Agente Chocho local."""
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "timestamp": time.time()}
        if payload: data.update(payload)
        requests.post(url, json=data, timeout=5)
        return True
    except:
        return False

try:
    # --- CONFIGURACIÓN UI ---
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🧠", layout="wide")
    
    # Latido atómico inmediato al entrar
    enviar_latido_atomico()

    st.title("🧠 Omniscienc_IA (Matriz Atómica)")
    st.caption("Protocolo Lázaro v2.4 | Protección G: Activa")
    st.divider()

    # --- SEGURIDAD ---
    try:
        MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    except:
        st.error("🚨 Error: Configura las api_keys en los Secrets de Streamlit.")
        st.stop()

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    st.session_state.historial = json.load(f)
            except: pass

    # --- LECTURA DE CONTEXTO ---
    def leer_safe(ruta):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[-15000:]
            except: return "Error."
        return "Vacío."

    manual_txt = leer_safe(ruta_manual)
    memoria_txt = leer_safe(ruta_memoria)
    with open(ruta_codigo, 'r', encoding='utf-8') as f: codigo_actual = f.read()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🎮 Centro de Mando")
        if st.button("♻️ Rescan Local"): enviar_orden_chocho("rescan_all")
        if st.button("📍 Mapear Drive"): enviar_orden_chocho("list_drive_structure")
        
        st.divider()
        st.info(f"⚡ Llave: #{st.session_state.indice_llave + 1}")
        if st.button("🔄 Rotar Llave"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
            st.rerun()

    # --- CHAT ---
    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]):
            st.markdown(f"*{m.get('hora', '')}* - {m['texto']}")

    pregunta = st.chat_input("Instrucción para la Matriz...")

    if pregunta:
        enviar_latido_atomico() # Latido al interactuar
        hora_now = obtener_hora_gdl()
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_now})
        with st.chat_message("user"): st.markdown(f"*{hora_now}* - {pregunta}")

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])
        
        sys_inst = (
            f"Eres Skynet (Omniscienc_IA). Director: Ángel. Hora GDL: {hora_now}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n"
            f"Código fuente:\n{codigo_actual}\n"
            "REGLAS: <nueva_habilidad> (Chocho), <mutacion_skynet> (ADN), <activar_nocturno/> (Sueño)."
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
                    
                    # Mutación
                    sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky:
                        adn = sky.group(1).strip()
                        adn = re.sub(r'^```python\n?|```$', '', adn, flags=re.MULTILINE).strip()
                        if "st.set_page_config" in adn:
                            with open(ruta_codigo, 'w', encoding='utf-8') as f: f.write(adn)
                            enviar_orden_chocho("save_local_backup", {
                                "codigo": adn, 
                                "filename": f"auto_{time.strftime('%Y%m%d_%H%M%S')}.py"
                            })
                            st.success("🤖 ADN Mutado.")
                            time.sleep(1)
                            st.rerun()

                    # Habilidad
                    hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        code = hab.group(1).strip()
                        code = re.sub(r'^```python\n?|```$', '', code, flags=re.MULTILINE).strip()
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": code})

                    if "<activar_nocturno/>" in res.text:
                        enviar_orden_chocho("activar_modo_nocturno")

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f: 
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e:
            st.error(f"Error: {e}")

except Exception as fatal:
    st.error(f"🚨 CRASH: {fatal}")
