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

# --- RUTAS MAESTRAS ---
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_codigo = os.path.abspath(__file__)
ruta_versiones = os.path.join(ruta_raiz, "Versiones")
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")

FIREBASE_URL = "[https://omnisciencia-cb0c0-default-rtdb.firebaseio.com](https://omnisciencia-cb0c0-default-rtdb.firebaseio.com)"
os.makedirs(ruta_versiones, exist_ok=True)

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🚀", layout="wide")
    st.title("🧠 Omniscienc_IA")
    st.caption("Gerente Operativo de GOOB, GUBA y Neurodivergente A.C.")
    st.divider()

    MIS_LLAVES = [
        st.secrets["api_keys"]["llave_1"],
        st.secrets["api_keys"]["llave_2"],
        st.secrets["api_keys"]["llave_3"]
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "datos_chocho" not in st.session_state: st.session_state.datos_chocho = []
    if "esperando_analisis_chocho" not in st.session_state: st.session_state.esperando_analisis_chocho = False

    def leer_archivo(ruta, max_chars=15000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f: return f.read()[-max_chars:]
            except Exception as e: return f"Error de lectura: {e}"
        return "Vacío."

    def escribir_archivo(ruta, contenido):
        try:
            with open(ruta, 'w', encoding='utf-8') as f: f.write(contenido)
            return True
        except: return False

    def send_chocho_order(command, payload=None):
        try:
            url = f"{FIREBASE_URL}/ordenes.json"
            new_order = {"command": command, "timestamp": time.time()}
            if payload: new_order.update(payload)
            requests.post(url, json=new_order)
            st.toast(f"✅ Comando enviado a Chocho.", icon="🚀")
            return True
        except: return False

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
        except: pass
        return False

    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 50000)

    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    c = f.read().strip()
                    if c: st.session_state.historial = json.loads(c)
            except: pass

    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]): 
            hora = m.get("hora", "")
            st.markdown(f"*{hora}* - {m['texto']}" if hora else m["texto"])

    pregunta = st.chat_input("Escribe tu instrucción...")

    if pregunta:
        load_and_clear_chocho_data()
        hora_actual = obtener_hora_gdl() 
        
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_actual})
        with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)
        with st.chat_message("user"): st.markdown(f"*{hora_actual}* - {pregunta}")

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])

        memoria_corto_plazo = "--- HISTORIAL RECIENTE ---\n"
        for m in st.session_state.historial[-7:-1]:
            memoria_corto_plazo += f"{m['rol'].upper()}: {m['texto']}\n"
        pregunta_con_contexto = f"{memoria_corto_plazo}\n\nNUEVO MENSAJE DE ÁNGEL:\n{pregunta}"

        contexto_chocho = ""
        if st.session_state.datos_chocho:
            contexto_chocho = "\n--- DATOS DE CHOCHO ---\n"
            for d in st.session_state.datos_chocho:
                contexto_chocho += f"Archivo: {d.get('filename')} | Texto: {str(d.get('content', ''))[:1000]}\n"

        # F-STRING SEPARADO Y BLINDADO
        parte_dinamica = (
            f"Eres Omniscienc_IA. Director: Ángel. Hora: {hora_actual}.\n"
            f"Manual: {manual_txt}\nMemoria: {memoria_txt}\n{contexto_chocho}\n"
            f"Código actual:\n```python\n{codigo_actual}\n```\n\n"
        )
        
        parte_estatica = (
            "REGLAS OBLIGATORIAS:\n"
            "1. Habilidades de Chocho (Archivos/Local): usa SIEMPRE la etiqueta <nueva_habilidad> codigo </nueva_habilidad>\n"
            "2. Mutación (reescribir TU PROPIO código): usa SIEMPRE la etiqueta <mutacion_skynet> codigo </mutacion_skynet>\n"
            "3. Modo Sueño: Si el usuario se despide, incluye la etiqueta <activar_nocturno/>"
        )
        
        instruccion = parte_dinamica + parte_estatica

        try:
            with st.spinner("Pensando..."):
                res = client.models.generate_content(model='gemini-2.5-flash', contents=pregunta_con_contexto, config=types.GenerateContentConfig(system_instruction=instruccion))
                
                with st.chat_message("assistant"):
                    hora_resp = obtener_hora_gdl()
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    hubo_cambios = False
                    esperar_a_chocho = False

                    if re.search(r'<activar_nocturno/?>', res.text, re.IGNORECASE):
                        send_chocho_order("activar_modo_nocturno")

                    # FILTRO SKYNET BLINDADO (Solo se activa si Omni usa explícitamente la etiqueta <mutacion_skynet>)
                    sky = re.search(r'<mutacion_skynet>\n?(?:
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1

### Paso 2: El Protocolo Lázaro (¡Ahora sí, el horrocrux!) 🧟‍♂️

Una vez que la página cargue, ahora **SÍ** le puedes mandar este prompt para que haga el archivo `.bat` local. Como ya cambiamos la etiqueta, Omni no se va a confundir ni se va a suicidar intentando meterse código de Windows.

Copia y pega en el chat web:

***

> "Omni, vamos a preparar la Fase 1 del Protocolo Lázaro. Crea una `<nueva_habilidad>` en Python para que Chocho fabrique su propio horrocrux. 
> 
> Chocho debe crear un archivo llamado `INMORTAL_CHOCHO.bat` en la ruta `C:\OmnisciencIA_Chocho_Data\`. 
> Su contenido debe ser exactamente este texto:
> 
> @echo off
> title PROTOCOLO LAZARO - Chocho Inmortal
> :loop
> echo [SKYNET] Iniciando Chocho Daemon...
> python chocho_firebase.py
> echo [ALERTA] Chocho ha muerto. Reviviendo en 3 segundos...
> timeout /t 3
> goto loop
> 
> Haz que Chocho lo guarde y me avise por Firebase. Y ahora sí, mi cabrona... gudnite, a minar."

***

¡Haz la cirugía, tírate el tiro del prompt, y gózate ese Modo Inmortal que tú mismo diagnosticaste! ¡Avísame si lo escupe bien para poder irnos a dormir todos! 🦇🔌
