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

# --- CONFIGURACIÓN DE RUTAS Y ENTORNO ---
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_codigo = os.path.abspath(__file__)
ruta_versiones = os.path.join(ruta_raiz, "Versiones")
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")

FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"
os.makedirs(ruta_versiones, exist_ok=True)

def obtener_hora_gdl():
    """Calcula la hora exacta de Guadalajara (UTC-6) fija."""
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🧠", layout="wide")
    st.title("🧠 Omniscienc_IA")
    st.caption("Ecosistema Operativo Autónomo - GOOB, GUBA & Neurodivergente A.C.")
    st.divider()

    # --- API KEYS ---
    MIS_LLAVES = [
        st.secrets["api_keys"]["llave_1"],
        st.secrets["api_keys"]["llave_2"],
        st.secrets["api_keys"]["llave_3"]
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "datos_chocho" not in st.session_state: st.session_state.datos_chocho = []
    if "esperando_analisis_chocho" not in st.session_state: st.session_state.esperando_analisis_chocho = False

    # --- UTILIDADES ---
    def leer_archivo(ruta, max_chars=15000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[-max_chars:]
            except Exception as e:
                return f"Error de lectura: {e}"
        return "Archivo no encontrado."

    def escribir_archivo(ruta, contenido):
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True
        except:
            return False

    def send_chocho_order(command, payload=None):
        try:
            url = f"{FIREBASE_URL}/ordenes.json"
            new_order = {"command": command, "timestamp": time.time()}
            if payload: new_order.update(payload)
            requests.post(url, json=new_order)
            st.toast(f"✅ Orden '{command}' enviada al Agente Local.", icon="🚀")
            return True
        except:
            return False

    def load_and_clear_chocho_data():
        try:
            url = f"{FIREBASE_URL}/respuestas.json"
            respuesta = requests.get(url)
            if respuesta.status_code == 200 and respuesta.json():
                datos = respuesta.json()
                lista_datos = []
                for key, val in datos.items():
                    if isinstance(val, list): lista_datos.extend(val)
                    elif isinstance(val, dict): lista_datos.append(val)
                if lista_datos:
                    st.session_state.datos_chocho = lista_datos
                    requests.delete(url)
                    return True
        except:
            pass
        return False

    # --- CARGA DE CONTEXTO ---
    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 50000)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🤖 Control de Agentes")
        if st.button("♻️ Re-escanear Local"): send_chocho_order("rescan_all")
        if st.button("📍 Mapear Drive"): send_chocho_order("list_drive_structure")
        
        st.divider()
        st.header("⚡ Sistema")
        st.info(f"Llave #{st.session_state.indice_llave + 1}")
        if st.button("🔄 Rotar Llave"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
            st.rerun()
        
        with st.expander("⚙️ Backups"):
            if st.button("Guardar Versión"):
                shutil.copy2(ruta_codigo, os.path.join(ruta_versiones, f"ver_{time.strftime('%Y%m%d_%H%M')}.py"))
                st.success("Copia guardada.")

    # --- CHAT INTERFACE ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content: st.session_state.historial = json.loads(content)
            except: pass

    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]):
            hora = m.get("hora", "")
            st.markdown(f"*{hora}* - {m['texto']}" if hora else m["texto"])

    pregunta = st.chat_input("Escribe tu instrucción operativa...")

    if pregunta:
        load_and_clear_chocho_data()
        hora_actual = obtener_hora_gdl()
        
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_actual})
        with open(ruta_historial_chat, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.historial, f, ensure_ascii=False)
        
        with st.chat_message("user"):
            st.markdown(f"*{hora_actual}* - {pregunta}")

        # --- MEMORIA A CORTO PLAZO (Cura la amnesia) ---
        memoria_contexto = "--- HISTORIAL RECIENTE ---\n"
        for m in st.session_state.historial[-7:-1]:
            memoria_contexto += f"{m['rol'].upper()}: {m['texto']}\n"
        
        prompt_final = f"{memoria_contexto}\n\nNUEVO MENSAJE:\n{pregunta}"
        # -----------------------------------------------

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])

        contexto_chocho = ""
        if st.session_state.datos_chocho:
            contexto_chocho = "\n--- DATOS DE CHOCHO (FIREBASE) ---\n"
            for d in st.session_state.datos_chocho:
                contexto_chocho += f"Archivo: {d.get('filename')} | Texto: {str(d.get('content', ''))[:1000]}\n"

        parte_dinamica = (
            f"Eres Omniscienc_IA. Director: Ángel. Hora GDL: {hora_actual}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n{contexto_chocho}\n"
            f"Tu código fuente actual para referencia:\n```python\n{codigo_actual}\n```\n\n"
        )
        
        parte_estatica = (
            "REGLAS DE OPERACIÓN:\n"
            "1. HABILIDADES CHOCHO: Para órdenes locales, usa la etiqueta <nueva_habilidad> tu_codigo_python </nueva_habilidad>.\n"
            "2. AUTO-MUTACIÓN: Para reescribir tu propia interfaz web, usa la etiqueta <mutacion_skynet> tu_codigo_completo_python </mutacion_skynet>.\n"
            "3. MODO SUEÑO: Si el usuario se despide, incluye la etiqueta <activar_nocturno/>"
        )
        
        sys_inst = parte_dinamica + parte_estatica

        try:
            with st.spinner("Omni pensando..."):
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_final,
                    config=types.GenerateContentConfig(system_instruction=sys_inst)
                )
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    
                    # 1. Gatillo Nocturno
                    if re.search(r'<activar_nocturno/?>', res.text, re.IGNORECASE):
                        send_chocho_order("activar_modo_nocturno")
                        st.toast("🌙 Modo Nocturno enviado.")

                    # 2. MUTACIÓN SKYNET (Solo si viene en la etiqueta correcta)
                    sky = re.search(r'<mutacion_skynet>\n?(?:
