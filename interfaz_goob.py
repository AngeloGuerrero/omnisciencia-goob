import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import openpyxl
import pdfplumber
import os
import time
import re
import shutil
import datetime
import json
import requests
from PIL import Image
import io

# --- RUTAS MAESTRAS (Adaptadas a la Nube) ---
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_codigo = os.path.abspath(__file__)
ruta_versiones = os.path.join(ruta_raiz, "Versiones")
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")

# --- FIREBASE URL ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

os.makedirs(ruta_versiones, exist_ok=True)

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🚀", layout="wide")

    # --- CSS MAGIA PARA ENCABEZADO FIJO ---
    st.markdown("""
        <style>
            div[data-testid="stVerticalBlock"] > div:first-child {
                position: sticky;
                top: 0;
                z-index: 999;
                background-color: #0e1117;
                padding-top: 1rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #333;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🧠 Omniscienc_IA")
    st.caption("Gerente Operativo de GOOB, GUBA y Neurodivergente A.C.")
    st.divider()

    # --- LECTURA SEGURA DE LLAVES (SECRETS) ---
    MIS_LLAVES = [
        st.secrets["api_keys"]["llave_1"],
        st.secrets["api_keys"]["llave_2"],
        st.secrets["api_keys"]["llave_3"]
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "last_generated_code" not in st.session_state: st.session_state.last_generated_code = None
    if "datos_chocho" not in st.session_state: st.session_state.datos_chocho = []

    def leer_archivo(ruta, max_chars=15000):
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8', errors='ignore') as f: return f.read()[-max_chars:]
            except Exception as e: return f"Error de lectura: {e}"
        return "Vacío."

    def escribir_archivo(ruta, contenido):
        try:
            if ruta in [ruta_manual, ruta_memoria]:
                ts = time.strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(ruta_raiz, "backups_knowledge_files")
                os.makedirs(backup_dir, exist_ok=True)
                if os.path.exists(ruta): shutil.copy2(ruta, os.path.join(backup_dir, f"{os.path.basename(ruta)}_{ts}.bak"))
            with open(ruta, 'w', encoding='utf-8') as f: f.write(contenido)
            return True
        except: return False

    # --- Función para mandar órdenes o Habilidades a Firebase ---
    def send_chocho_order(command, payload=None):
        try:
            url = f"{FIREBASE_URL}/ordenes.json"
            new_order = {"command": command, "timestamp": time.time()}
            if payload: new_order.update(payload)
            requests.post(url, json=new_order)
            st.toast(f"✅ Comando/Habilidad '{command}' enviada al puente Firebase.", icon="🚀")
            return True
        except Exception as e:
            st.error(f"Fallo al enviar a la nube: {e}")
            return False

    def load_and_clear_chocho_data():
        try:
            url = f"{FIREBASE_URL}/respuestas.json"
            respuesta = requests.get(url)
            if respuesta.status_code == 200 and respuesta.json():
                datos = respuesta.json()
                lista_datos = [val for key, val in datos.items()]
                if lista_datos:
                    st.session_state.datos_chocho = lista_datos
                    st.toast(f"📥 {len(lista_datos)} reportes recibidos desde Firebase.")
                    requests.delete(url)
        except Exception as e:
            pass

    # --- Función para procesar Archivos Subidos Manualmente ---
    def procesar_archivo_subido(archivo):
        if archivo.type.startswith('image/'):
            return Image.open(archivo)
        elif archivo.type == 'application/pdf':
            texto = ""
            with pdfplumber.open(archivo) as pdf:
                for page in pdf.pages: texto += page.extract_text() or ""
            return texto
        elif archivo.type == 'text/plain':
            return archivo.read().decode("utf-8")
        else:
            return f"Formato no soportado: {archivo.type}"

    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 50000)

    # --- BARRA LATERAL (CONTROLES Y UPLOADER) ---
    with st.sidebar:
        st.header("📎 Analizador Visual")
        archivo_usuario = st.file_uploader("Sube una imagen o archivo para Omniscienc_IA", type=["png", "jpg", "jpeg", "pdf", "txt"])
        contenido_archivo = None
        if archivo_usuario:
            contenido_archivo = procesar_archivo_subido(archivo_usuario)
            st.success("✅ Archivo cargado. Haz tu pregunta en el chat.")

        st.divider()
        st.header("🤖 Control de Agentes (Chocho)")
        if st.button("♻️ Re-escanear Archivos"):
            send_chocho_order("rescan_all")
        if st.button("📍 Mapear Carpetas de Drive"):
            send_chocho_order("list_drive_structure", {"account": "goob_drive"})
            st.info("Orden enviada a la nube.")

        st.divider()
        st.header("⚡ Estado del Sistema")
        st.info(f"Usando Llave #{st.session_state.indice_llave + 1}")
        if st.button("🔄 Cambiar Llave Manualmente"):
            st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
            st.rerun()

        st.divider()
        st.header("💬 Controles de Chat")
        if st.button("⬇️ Ir al mensaje más reciente"):
            st.components.v1.html("<script>var s = parent.document.querySelector('.main .block-container'); if(s) s.scrollTop = s.scrollHeight;</script>", height=0)

        st.divider()
        with st.expander("⚙️ Autogestión de Código"):
            if st.button("Guardar Versión Actual"):
                shutil.copy2(ruta_codigo, os.path.join(ruta_versiones, f"version_{time.strftime('%Y%m%d_%H%M%S')}.py"))
                st.success("✅ Versión guardada.")
            if st.button("🛠️ Aplicar IA Código", disabled=(st.session_state.last_generated_code is None)):
                if st.session_state.last_generated_code:
                    shutil.copy2(ruta_codigo, os.path.join(ruta_versiones, f"backup_{time.strftime('%Y%m%d_%H%M%S')}.py"))
                    with open(ruta_codigo, 'w', encoding='utf-8') as f: f.write(st.session_state.last_generated_code)
                    st.session_state.last_generated_code = None
                    st.success("✅ CÓDIGO APLICADO. Presiona F5.")

    # --- CHAT Y RESPUESTAS ---
    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    c = f.read().strip()
                    if c: st.session_state.historial = json.loads(c)
            except: pass

    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]): st.markdown(m["texto"])

    pregunta = st.chat_input("Escribe tu instrucción operativa...")

    if pregunta:
        load_and_clear_chocho_data()
        st.session_state.historial.append({"rol": "user", "texto": pregunta})
        with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)
        with st.chat_message("user"): st.markdown(pregunta)

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])

        contexto_chocho = ""
        if st.session_state.datos_chocho:
            contexto_chocho = "\n\n--- DATOS DE CHOCHO (DESDE FIREBASE) ---\n"
            for d in st.session_state.datos_chocho:
                content_for_chocho = str(d.get('content'))[:1000]
                contexto_chocho += f"Archivo: {d.get('filename')} | Estado: {d.get('status')}\nTexto: {content_for_chocho}\n\n"

        # ¡AQUÍ ESTÁ EL FIX DE LAS LLAVES DOBLES {{ }} !
        instruccion = f"""Eres Omniscienc_IA. Director: Ángel.
        Manual: {manual_txt}
        Memoria: {memoria_txt}
        {contexto_chocho}
        Código actual: ```python\n{codigo_actual}\n```

        REGLAS PARA CREAR HABILIDADES DINÁMICAS (PLUGINS PARA CHOCHO):
        Si el usuario te pide a ti o a Chocho hacer algo en la computadora local que tú no puedes hacer desde la nube, DEBES redactar un mini-script de Python.
        Usa la etiqueta <nueva_habilidad> tu_codigo_python_aqui </nueva_habilidad>. 
        El código debe ser auto-contenido, importar sus librerías y usar la función 'send_to_firebase([{{ "filename": "Reporte_Habilidad", "content": "tus_resultados" }}])' para devolverte los datos. Chocho lo ejecutará.

        Si debes modificar tu propio código de Streamlit, usa un bloque ```python
        Para actualizar manual usa <nuevo_manual>...</nuevo_manual>
        Para actualizar memoria usa <nueva_memoria>...</nueva_memoria>"""

        try:
            with st.spinner("Pensando..."):
                if contenido_archivo and isinstance(contenido_archivo, Image.Image):
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=[pregunta, contenido_archivo], config=types.GenerateContentConfig(system_instruction=instruccion))
                elif contenido_archivo and isinstance(contenido_archivo, str):
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=f"Archivo subido por usuario:\n{contenido_archivo}\n\nInstrucción: {pregunta}", config=types.GenerateContentConfig(system_instruction=instruccion))
                else:
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=pregunta, config=types.GenerateContentConfig(system_instruction=instruccion))
                
                with st.chat_message("assistant"):
                    st.markdown(res.text)
                    hubo_cambios = False

                    cod = re.search(r'```python\n?(.*?)\n?```', res.text, re.DOTALL)
                    if cod and "st.set_page_config" in cod.group(1):
                        st.session_state.last_generated_code = cod.group(1).strip()
                        st.toast("🚨 ¡Código Streamlit listo en el panel lateral!", icon="⚠️")
                        hubo_cambios = True

                    hab = re.search(r'<nueva_habilidad>\n?(.*?)\n?</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        send_chocho_order("ejecutar_habilidad", {"codigo": hab.group(1).strip()})
                        hubo_cambios = True

                    man = re.search(r'<nuevo_manual>\n?(.*?)\n?</nuevo_manual>', res.text, re.DOTALL)
                    if man: escribir_archivo(ruta_manual, man.group(1).strip()); hubo_cambios = True

                    mem = re.search(r'<nueva_memoria>\n?(.*?)\n?</nueva_memoria>', res.text, re.DOTALL)
                    if mem: escribir_archivo(ruta_memoria, mem.group(1).strip()); hubo_cambios = True

                st.session_state.historial.append({"rol": "assistant", "texto": res.text})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)

                if hubo_cambios: time.sleep(1); st.rerun()

        except Exception as e:
            if "429" in str(e) or "Exhausted" in str(e):
                st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
                st.rerun()
            else: st.error(f"Error técnico: {e}")

except Exception as global_crash:
    st.error("🚨 ¡CRASH DEL SISTEMA!")
    st.warning(f"Error detectado: {global_crash}")
