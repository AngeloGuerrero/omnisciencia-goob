import streamlit as st
from google import genai
from google.genai import types
import os
import time
import re
import shutil
import json
import requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DE IDENTIDAD Y RUTAS ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_codigo = os.path.abspath(__file__)
ruta_versiones = os.path.join(ruta_raiz, "Versiones")
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"
os.makedirs(ruta_versiones, exist_ok=True)

def obtener_hora_gdl():
    """Hora exacta de Guadalajara (UTC-6)."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    """Protocolo Lázaro: Informa a Chocho que Skynet sigue viva (Heartbeat Optimizado)."""
    try:
        url = f"{FIREBASE_URL}/status/skynet.json"
        data = {
            "last_heartbeat": time.time(), 
            "hora": obtener_hora_gdl(), 
            "status": "ALIVE",
            "server": "Streamlit Cloud"
        }
        # Timeout ultra-corto para no trabar la interfaz
        requests.put(url, json=data, timeout=1.5)
    except:
        pass

try:
    # --- INICIO DE SISTEMA ---
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🧠", layout="wide")
    
    # Latido vital al arranque
    enviar_latido() 

    st.title("🧠 Omniscienc_IA (Skynet Inmortal)")
    st.caption("Ecosistema de Alta Disponibilidad - Protocolo Lázaro Balanceado")
    
    # --- PANEL DE CONTROL SIDEBAR ---
    with st.sidebar:
        st.header("🎮 Centro de Control")
        st.info(f"📍 Zona Horaria: Guadalajara\n⏰ {obtener_hora_gdl()}")
        
        if st.button("♻️ Rescan Archivos"): 
            enviar_latido()
            send_chocho_order("rescan_all")
            
        st.divider()
        if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
        st.info(f"⚡ Matriz: Llave #{st.session_state.indice_llave + 1}")
        
        if st.button("🔄 Rotar API Key"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % 3
            st.rerun()

    # --- CARGA DE CONTEXTO ---
    def leer_archivo(ruta, max_chars=15000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[-max_chars:]
            except: return "Error."
        return "Vacío."

    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 30000)

    # --- CHAT ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    st.session_state.historial = json.load(f)
            except: pass

    for m in st.session_state.historial[-8:]:
        with st.chat_message(m["rol"]):
            st.markdown(f"*{m.get('hora', '')}* - {m['texto']}")

    pregunta = st.chat_input("Escribe tu instrucción operativa...")

    if pregunta:
        enviar_latido()
        hora_now = obtener_hora_gdl()
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_now})
        
        with st.chat_message("user"): st.markdown(f"*{hora_now}* - {pregunta}")

        # Memoria Corto Plazo
        ctx_reciente = "--- HISTORIAL RECIENTE ---\n"
        for m in st.session_state.historial[-5:-1]:
            ctx_reciente += f"{m['rol'].upper()}: {m['texto']}\n"
        
        prompt_full = f"{ctx_reciente}\n\nNUEVO MENSAJE:\n{pregunta}"

        llave = st.secrets["api_keys"][f"llave_{st.session_state.indice_llave + 1}"]
        client = genai.Client(api_key=llave)

        sys_inst = (
            f"Eres Skynet (Omniscienc_IA). Director: Ángel. Hora GDL: {hora_now}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n"
            f"Tu código fuente:\n```python\n{codigo_actual}\n```\n"
            "REGLAS: Habilidad Chocho: <nueva_habilidad>, Mutación: <mutacion_skynet>, Sueño: <activar_nocturno/>"
        )

        try:
            with st.spinner("Skynet pensando..."):
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_full,
                    config=types.GenerateContentConfig(system_instruction=sys_inst)
                )
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    
                    if "<activar_nocturno/>" in res.text:
                        url = f"{FIREBASE_URL}/ordenes.json"
                        requests.post(url, json={"command": "activar_modo_nocturno", "timestamp": time.time()})

                    # MUTACIÓN SKYNET
                    sky_match = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky_match:
                        nuevo_adn = sky_match.group(1).strip()
                        nuevo_adn = re.sub(r'^```python\n?|```$', '', nuevo_adn, flags=re.MULTILINE).strip()
                        with open(ruta_codigo, 'w', encoding='utf-8') as f: f.write(nuevo_adn)
                        st.success("🤖 ADN Mutado.")
                        time.sleep(1)
                        st.rerun()

                    # HABILIDAD CHOCHO
                    hab_match = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab_match:
                        code_hab = hab_match.group(1).strip()
                        code_hab = re.sub(r'^```python\n?|```$', '', code_hab, flags=re.MULTILINE).strip()
                        url = f"{FIREBASE_URL}/ordenes.json"
                        requests.post(url, json={"command": "ejecutar_habilidad", "codigo": code_hab, "timestamp": time.time()})
                        st.toast("🚀 Habilidad enviada a Chocho.")

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e:
            st.error(f"Error: {e}")

except Exception as fatal:
    st.error(f"🚨 CRASH: {fatal}")
