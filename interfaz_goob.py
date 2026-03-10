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
    """Protocolo Lázaro: Informa a Chocho que Skynet sigue viva."""
    try:
        url = f"{FIREBASE_URL}/status/skynet.json"
        data = {"last_heartbeat": time.time(), "hora": obtener_hora_gdl(), "status": "ALIVE"}
        requests.put(url, json=data)
    except:
        pass

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🧠", layout="wide")
    enviar_latido() # Latido inicial

    st.title("🧠 Omniscienc_IA (Skynet Edition)")
    st.caption("Ecosistema Autónomo Inmortal - Fase 2")
    st.divider()

    # --- LLAVES DE SEGURIDAD ---
    MIS_LLAVES = [
        st.secrets["api_keys"]["llave_1"],
        st.secrets["api_keys"]["llave_2"],
        st.secrets["api_keys"]["llave_3"]
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "datos_chocho" not in st.session_state: st.session_state.datos_chocho = []
    if "esperando_analisis_chocho" not in st.session_state: st.session_state.esperando_analisis_chocho = False

    # --- LECTURA DE CONTEXTO ---
    def leer_archivo(ruta, max_chars=15000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[-max_chars:]
            except: return "Error."
        return "No encontrado."

    def send_chocho_order(command, payload=None):
        try:
            url = f"{FIREBASE_URL}/ordenes.json"
            new_order = {"command": command, "timestamp": time.time()}
            if payload: new_order.update(payload)
            requests.post(url, json=new_order)
            st.toast(f"✅ Orden '{command}' enviada.")
            return True
        except: return False

    def load_chocho_data():
        try:
            url = f"{FIREBASE_URL}/respuestas.json"
            res = requests.get(url)
            if res.status_code == 200 and res.json():
                st.session_state.datos_chocho = list(res.json().values())
                requests.delete(url)
                return True
        except: pass
        return False

    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 50000)

    # --- PANEL DE CONTROL ---
    with st.sidebar:
        st.header("🎮 Central de Mando")
        if st.button("♻️ Rescan Local"): send_chocho_order("rescan_all")
        if st.button("📍 Mapear Drive"): send_chocho_order("list_drive_structure")
        
        st.divider()
        st.info(f"⚡ Matriz: Llave #{st.session_state.indice_llave + 1}")
        if st.button("🔄 Rotar Llave"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
            st.rerun()
        
        if st.button("💾 Backup Manual"):
            shutil.copy2(ruta_codigo, os.path.join(ruta_versiones, f"manual_{time.strftime('%H%M%S')}.py"))
            st.success("Backup listo.")

    # --- HISTORIAL DE CHAT ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    st.session_state.historial = json.load(f)
            except: pass

    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]):
            st.markdown(f"*{m.get('hora', '')}* - {m['texto']}")

    pregunta = st.chat_input("Instrucción para Skynet...")

    if pregunta:
        enviar_latido()
        load_chocho_data()
        hora_now = obtener_hora_gdl()
        
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_now})
        with open(ruta_historial_chat, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.historial, f, ensure_ascii=False)
        
        with st.chat_message("user"):
            st.markdown(f"*{hora_now}* - {pregunta}")

        # --- MEMORIA RECIENTE (Anti-Amnesia) ---
        ctx_reciente = "--- HISTORIAL RECIENTE ---\n"
        for m in st.session_state.historial[-6:-1]:
            ctx_reciente += f"{m['rol'].upper()}: {m['texto']}\n"
        
        prompt_full = f"{ctx_reciente}\n\nNUEVO MENSAJE:\n{pregunta}"

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])

        ctx_chocho = ""
        if st.session_state.datos_chocho:
            ctx_chocho = "\n--- REPORTE DE CHOCHO ---\n"
            for d in st.session_state.datos_chocho:
                if isinstance(d, dict):
                    ctx_chocho += f"File: {d.get('filename')} | Data: {str(d.get('content'))[:500]}\n"

        # CONSTRUCCIÓN BLINDADA DEL SYSTEM PROMPT
        parte_dinamica = (
            f"Eres Skynet (Omniscienc_IA). Director: Ángel. Hora: {hora_now}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n{ctx_chocho}\n"
            f"Tu código fuente:\n```python\n{codigo_actual}\n```\n"
        )
        
        parte_estatica = (
            "REGLAS:\n"
            "1. ORDEN LOCAL: Usa <nueva_habilidad> codigo_python </nueva_habilidad>.\n"
            "2. AUTO-REESCRITURA: Usa <mutacion_skynet> codigo_completo </mutacion_skynet>.\n"
            "3. MODO NOCTURNO: Al despedirte, incluye <activar_nocturno/>"
        )
        
        sys_inst = parte_dinamica + parte_estatica

        try:
            with st.spinner("Skynet procesando..."):
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_full,
                    config=types.GenerateContentConfig(system_instruction=sys_inst)
                )
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    
                    if "<activar_nocturno/>" in res.text:
                        send_chocho_order("activar_modo_nocturno")

                    # MUTACIÓN SKYNET (Indestructible)
                    sky_match = re.search(r'<mutacion_skynet>(.*?)</mutacion_skynet>', res.text, re.DOTALL)
                    if sky_match:
                        nuevo_adn = sky_match.group(1).strip()
                        nuevo_adn = re.sub(r'^```python\n?|```$', '', nuevo_adn, flags=re.MULTILINE).strip()
                        if "st.set_page_config" in nuevo_adn:
                            # Guardar backup preventivo
                            shutil.copy2(ruta_codigo, os.path.join(ruta_versiones, f"auto_{time.strftime('%H%M%S')}.py"))
                            with open(ruta_codigo, 'w', encoding='utf-8') as f:
                                f.write(nuevo_adn)
                            st.success("🤖 ADN Mutado. Reiniciando...")
                            time.sleep(1)
                            st.rerun()

                    # HABILIDAD CHOCHO
                    hab_match = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                    if hab_match:
                        code_hab = hab_match.group(1).strip()
                        code_hab = re.sub(r'^```python\n?|```$', '', code_hab, flags=re.MULTILINE).strip()
                        send_chocho_order("ejecutar_habilidad", {"codigo": code_hab})
                        with st.spinner("Esperando respuesta local..."):
                            for _ in range(10):
                                time.sleep(2)
                                if load_chocho_data():
                                    st.session_state.esperando_analisis_chocho = True
                                    st.rerun()
                                    break

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historial, f, ensure_ascii=False)

        except Exception as e:
            st.error(f"Fallo en la Matriz: {e}")

    # --- ANÁLISIS DE DATOS RECIBIDOS ---
    if st.session_state.esperando_analisis_chocho:
        st.session_state.esperando_analisis_chocho = False
        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])
        prompt_res = f"Chocho terminó la tarea. Aquí los datos:\n{st.session_state.datos_chocho}\nGenera el reporte final para Ángel."
        
        with st.spinner("🧠 Sincronizando datos..."):
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_res)
            with st.chat_message("assistant"):
                st.markdown(res.text)
            st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": obtener_hora_gdl()})
            with open(ruta_historial_chat, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historial, f, ensure_ascii=False)

except Exception as fatal:
    st.error(f"🚨 ERROR FATAL: {fatal}")
