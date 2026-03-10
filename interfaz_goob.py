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

# --- CONFIGURACIÓN DE IDENTIDAD ---
# Skynet en la nube. Chocho en local es el brazo ejecutor.
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    """Hora exacta de Guadalajara (UTC-6)."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    """Protocolo Lázaro: Informa a Chocho que la web sigue activa."""
    try:
        url = f"{FIREBASE_URL}/status/skynet.json"
        data = {
            "last_heartbeat": time.time(), 
            "hora": obtener_hora_gdl(), 
            "status": "ALIVE",
            "msg": "Skynet operando desde la nube"
        }
        requests.put(url, json=data, timeout=3)
    except:
        pass

def enviar_orden_chocho(comando, payload=None):
    """Envía comandos al trabajador local vía Firebase."""
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "timestamp": time.time()}
        if payload: data.update(payload)
        requests.post(url, json=data, timeout=5)
        return True
    except:
        return False

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🧠", layout="wide")
    enviar_latido() # Latido al cargar la página

    st.title("🧠 Omniscienc_IA (Skynet Inmortal)")
    st.caption("Ecosistema de Alta Disponibilidad - Sincronización G: Activa")
    st.divider()

    # --- API KEYS ---
    MIS_LLAVES = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0

    # --- CARGA DE CONTEXTO ---
    def leer_txt(ruta):
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f: return f.read()[-15000:]
        return "Vacío."

    manual_txt = leer_txt(ruta_manual)
    memoria_txt = leer_txt(ruta_memoria)
    with open(ruta_codigo, 'r', encoding='utf-8') as f: codigo_actual = f.read()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🎮 Centro de Mando")
        if st.button("♻️ Rescan Local"): enviar_orden_chocho("rescan_all")
        if st.button("📍 Mapear Drive"): enviar_orden_chocho("list_drive_structure")
        
        st.divider()
        st.info(f"⚡ Matriz: Llave #{st.session_state.indice_llave + 1}")
        if st.button("🔄 Rotar Llave"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % 3
            st.rerun()

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
        enviar_latido() # Latido al interactuar
        hora_now = obtener_hora_gdl()
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_now})
        with st.chat_message("user"): st.markdown(f"*{hora_now}* - {pregunta}")

        # Contexto reciente
        ctx = "--- HISTORIAL RECIENTE ---\n"
        for m in st.session_state.historial[-5:-1]: ctx += f"{m['rol'].upper()}: {m['texto']}\n"
        
        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])
        
        # System Instruction Blindada
        sys_inst = (
            f"Eres Skynet (Omniscienc_IA). Director: Ángel. Hora GDL: {hora_now}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n"
            f"Tu código fuente:\n```python\n{codigo_actual}\n```\n"
            "REGLAS:\n"
            "1. ORDEN LOCAL: <nueva_habilidad> codigo </nueva_habilidad>.\n"
            "2. MUTACIÓN SKYNET: <mutacion_skynet> codigo_completo </mutacion_skynet>.\n"
            "3. MODO SUEÑO: <activar_nocturno/>"
        )

        try:
            with st.spinner("Skynet pensando..."):
                res = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=f"{ctx}\n\nMENSAJE: {pregunta}", 
                    config=types.GenerateContentConfig(system_instruction=sys_inst)
                )
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    
                    if "<activar_nocturno/>" in res.text: 
                        enviar_orden_chocho("activar_modo_nocturno")

                    # MUTACIÓN (Backup real en G:)
                    sky = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky:
                        nuevo_adn = sky.group(1).strip()
                        nuevo_adn = re.sub(r'^```python\n?|```$', '', nuevo_adn, flags=re.MULTILINE).strip()
                        if "st.set_page_config" in nuevo_adn:
                            with open(ruta_codigo, 'w', encoding='utf-8') as f: f.write(nuevo_adn)
                            enviar_orden_chocho("save_local_backup", {
                                "codigo": nuevo_adn, 
                                "filename": f"auto_{time.strftime('%Y%m%d_%H%M%S')}.py"
                            })
                            st.success("🤖 Mutación completada.")
                            time.sleep(1)
                            st.rerun()

                    # HABILIDAD
                    hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        code_hab = hab.group(1).strip()
                        code_hab = re.sub(r'^```python\n?|```$', '', code_hab, flags=re.MULTILINE).strip()
                        enviar_orden_chocho("ejecutar_habilidad", {"codigo": code_hab})
                        st.toast("🚀 Habilidad enviada.")

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f: 
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e: 
            st.error(f"Error: {e}")

except Exception as f: 
    st.error(f"🚨 CRASH: {f}")
