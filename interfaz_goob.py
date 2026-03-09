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

# --- RUTAS MAESTRAS ---
ruta_raiz = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
ruta_manual = os.path.join(ruta_raiz, "manual_guba.txt")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")
ruta_excel = r"G:\Mi unidad\2-GUBA\Cotizaciones\Formato de cotizaciones GUBA.xlsm"
ruta_fege = r"G:\Mi unidad\2-GUBA\Cotizaciones\FEGE"
ruta_codigo = os.path.abspath(__file__)
ruta_versiones = os.path.join(ruta_raiz, "Versiones")
ruta_historial_chat = os.path.join(ruta_raiz, "historial_chat.json")
ruta_puente_chocho = os.path.join(ruta_raiz, "chocho_datos_extraidos.json") 
ruta_ordenes_chocho = os.path.join(ruta_raiz, "omnisciencia_ordenes.json") 

os.makedirs(ruta_versiones, exist_ok=True)
os.makedirs(ruta_fege, exist_ok=True)

try:
    st.set_page_config(page_title="Omniscienc_IA", page_icon="🚀", layout="wide")
    st.title("🧠 Omniscienc_IA")
    st.caption("Gerente Operativo de GOOB, GUBA y Neurodivergente A.C.")
    st.divider()

    MIS_LLAVES = [
        "AIzaSyDy_IaOAwl4jpRY0hbBHK6UZoYb1dg_u3M",
        "AIzaSyDenmdZO6-bkKS0pReNxh3IXD_OSuSNmuk",
        "AIzaSyCOiyZ_WdbMzJfMe89tQ6EECDLyhePCOFE"
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "last_generated_code" not in st.session_state: st.session_state.last_generated_code = None
    if "datos_chocho" not in st.session_state: st.session_state.datos_chocho = []
    if "chocho_last_mod_time" not in st.session_state: st.session_state.chocho_last_mod_time = None

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

    # --- Función para mandar órdenes a Chocho ---
    def send_chocho_order(command, payload=None):
        try:
            orders = []
            if os.path.exists(ruta_ordenes_chocho) and os.path.getsize(ruta_ordenes_chocho) > 0:
                with open(ruta_ordenes_chocho, 'r', encoding='utf-8') as f:
                    try: orders = json.load(f)
                    except: pass

            new_order = {"command": command}
            if payload: new_order.update(payload)
            orders.append(new_order)

            with open(ruta_ordenes_chocho, 'w', encoding='utf-8') as f: json.dump(orders, f, ensure_ascii=False, indent=4)
            st.toast(f"✅ Orden '{command}' enviada al Agente Chocho.", icon="🚀")
            return True
        except Exception as e:
            st.error(f"Fallo al enviar orden: {e}")
            return False

    def load_and_clear_chocho_data():
        if os.path.exists(ruta_puente_chocho):
            current_mod_time = os.path.getmtime(ruta_puente_chocho)
            if st.session_state.chocho_last_mod_time is None or current_mod_time > st.session_state.chocho_last_mod_time:
                try:
                    with open(ruta_puente_chocho, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                    if file_content: 
                        new_data = json.loads(file_content)
                        if new_data: 
                            st.session_state.datos_chocho = new_data
                            st.toast(f"📥 {len(new_data)} nuevos reportes de Chocho recibidos.")
                            with open(ruta_puente_chocho, 'w', encoding='utf-8') as f: json.dump([], f)
                    st.session_state.chocho_last_mod_time = current_mod_time
                except Exception:
                    with open(ruta_puente_chocho, 'w', encoding='utf-8') as f: json.dump([], f)
                    st.session_state.chocho_last_mod_time = os.path.getmtime(ruta_puente_chocho)

    manual_txt = leer_archivo(ruta_manual)
    memoria_txt = leer_archivo(ruta_memoria)
    codigo_actual = leer_archivo(ruta_codigo, 50000)

    # --- BARRA LATERAL (CONTROLES) ---
    with st.sidebar:
        st.header("🤖 Control de Agentes (Chocho)")
        if st.button("♻️ Re-escanear Archivos"):
            send_chocho_order("rescan_all")
        if st.button("📍 Mapear Carpetas de Drive"):
            send_chocho_order("list_drive_structure", {"account": "goob_drive"})
            st.info("Chocho está creando el mapa de GOOB. Estará listo en unos segundos.")

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

    # --- LECTURA DE MAPAS DE DRIVE ---
    mapa_drive_str = ""
    mapa_file = os.path.join(ruta_raiz, "mapa_carpetas_goob_drive.json")
    if os.path.exists(mapa_file):
        try:
            with open(mapa_file, 'r', encoding='utf-8') as f:
                carpetas = json.load(f)
                mapa_drive_str = f"Carpetas en GOOB Drive detectadas: {len(carpetas)}\n(El mapa detallado está guardado en disco. Puedes consultarlo para saber las rutas exactas)."
        except: pass

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
            contexto_chocho = "\n\n--- DATOS DE CHOCHO ---\n"
            for d in st.session_state.datos_chocho:
                content_for_chocho = str(d.get('content'))[:1000]
                contexto_chocho += f"Archivo: {d.get('filename')} | Estado: {d.get('status')}\nTexto: {content_for_chocho}\n\n"

        # LA MAGIA ANTI-CRASH: Usando TRIPLE COMILLA para la f-string
        instruccion = f"""Eres Omniscienc_IA. Director: Ángel.
        Manual:
        {manual_txt}

        Memoria:
        {memoria_txt}

        {contexto_chocho}
        {mapa_drive_str}

        Código fuente actual:
        ```python
        {codigo_actual}
        ```

        Si debes modificar código, usa un bloque ```python
        Para actualizar manual usa <nuevo_manual>...</nuevo_manual>
        Para actualizar memoria usa <nueva_memoria>...</nueva_memoria>"""

        try:
            with st.spinner("Pensando..."):
                res = client.models.generate_content(model='gemini-2.5-flash', contents=pregunta, config=types.GenerateContentConfig(system_instruction=instruccion))
                with st.chat_message("assistant"):
                    st.markdown(res.text)
                    hubo_cambios = False

                    cod = re.search(r'```python\n?(.*?)\n?```', res.text, re.DOTALL)
                    if cod:
                        st.session_state.last_generated_code = cod.group(1).strip()
                        st.toast("🚨 ¡Código listo en el panel lateral!", icon="⚠️")
                        hubo_cambios = True

                    man = re.search(r'<nuevo_manual>\n?(.*?)\n?</nuevo_manual>', res.text, re.DOTALL)
                    if man:
                        escribir_archivo(ruta_manual, man.group(1).strip())
                        hubo_cambios = True

                    mem = re.search(r'<nueva_memoria>\n?(.*?)\n?</nueva_memoria>', res.text, re.DOTALL)
                    if mem:
                        escribir_archivo(ruta_memoria, mem.group(1).strip())
                        hubo_cambios = True

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
    try:
        archivos_backup = [os.path.join(ruta_versiones, f) for f in os.listdir(ruta_versiones) if f.startswith("backup_") and f.endswith(".py")]
        if archivos_backup:
            backup_reciente = max(archivos_backup, key=os.path.getctime)
            shutil.copy2(backup_reciente, ruta_codigo)
            st.success(f"✅ Restaurado desde: {os.path.basename(backup_reciente)}")
            st.info("🔄 PRESIONA F5 EN TU TECLADO PARA RECARGAR.")
    except: pass