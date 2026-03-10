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

    st.title("🧠 Omniscienc_IA")
    st.caption("Gerente Operativo de GOOB, GUBA y Neurodivergente A.C.")
    st.divider()

    MIS_LLAVES = [
        st.secrets["api_keys"]["llave_1"],
        st.secrets["api_keys"]["llave_2"],
        st.secrets["api_keys"]["llave_3"]
    ]

    if "indice_llave" not in st.session_state: st.session_state.indice_llave = 0
    if "last_generated_code" not in st.session_state: st.session_state.last_generated_code = None
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
            if ruta in [ruta_manual, ruta_memoria]:
                ts = time.strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(ruta_raiz, "backups_knowledge_files")
                os.makedirs(backup_dir, exist_ok=True)
                if os.path.exists(ruta): shutil.copy2(ruta, os.path.join(backup_dir, f"{os.path.basename(ruta)}_{ts}.bak"))
            with open(ruta, 'w', encoding='utf-8') as f: f.write(contenido)
            return True
        except: return False

    def send_chocho_order(command, payload=None):
        try:
            url = f"{FIREBASE_URL}/ordenes.json"
            new_order = {"command": command, "timestamp": time.time()}
            if payload: new_order.update(payload)
            requests.post(url, json=new_order)
            st.toast(f"✅ Comando '{command}' enviado al puente Firebase.", icon="🚀")
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
                lista_datos = []
                for key, val in datos.items():
                    if isinstance(val, list):
                        lista_datos.extend(val)
                    elif isinstance(val, dict):
                        lista_datos.append(val)
                if lista_datos:
                    st.session_state.datos_chocho = lista_datos
                    st.toast(f"📥 {len(lista_datos)} reportes recibidos desde Firebase.")
                    requests.delete(url)
                    return True
        except Exception as e:
            pass
        return False

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

    if "historial" not in st.session_state:
        st.session_state.historial = []
        if os.path.exists(ruta_historial_chat):
            try:
                with open(ruta_historial_chat, 'r', encoding='utf-8') as f:
                    c = f.read().strip()
                    if c: st.session_state.historial = json.loads(c)
            except: pass

    # --- PINTAMOS LOS MENSAJES CON LA HORA ---
    for m in st.session_state.historial[-10:]:
        with st.chat_message(m["rol"]): 
            hora = m.get("hora", "")
            if hora:
                st.markdown(f"*{hora}* - {m['texto']}")
            else:
                st.markdown(m["texto"])

    pregunta = st.chat_input("Escribe tu instrucción operativa...")

    # --- FLUJO 1: CUANDO TÚ PREGUNTAS ALGO ---
    if pregunta:
        load_and_clear_chocho_data()
        hora_actual = time.strftime("%I:%M %p") 
        
        st.session_state.historial.append({"rol": "user", "texto": pregunta, "hora": hora_actual})
        with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)
        with st.chat_message("user"): st.markdown(f"*{hora_actual}* - {pregunta}")

        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])

        contexto_chocho = ""
        if st.session_state.datos_chocho:
            contexto_chocho = "\n\n--- DATOS DE CHOCHO (DESDE FIREBASE) ---\n"
            for d in st.session_state.datos_chocho:
                content_for_chocho = str(d.get('content', ''))[:1000]
                contexto_chocho += f"Archivo: {d.get('filename', 'Desconocido')} | Estado: {d.get('status', 'N/A')}\nTexto: {content_for_chocho}\n\n"

        parte_dinamica = f"Eres Omniscienc_IA. Director: Ángel. La hora actual del sistema es {hora_actual}.\nManual: {manual_txt}\nMemoria: {memoria_txt}\n{contexto_chocho}\nCódigo actual: ```python\n{codigo_actual}\n```\n\n"
        
        parte_estatica = (
            "EL CEREBRO CENTRAL DE METADATOS:\n"
            "Ubicado en: J:\\Mi unidad\\OmnisciencIA_Chocho_Data\\Cerebro_Metadatos.json\n\n"
            "REGLAS PARA HABILIDADES DINÁMICAS (PLUGINS CHOCHO):\n"
            "Si necesitas leer, escribir o ejecutar algo localmente, usa un mini-script de Python dentro de <nueva_habilidad> tu_codigo </nueva_habilidad>. Usa 'send_to_firebase([{\"filename\": \"Reporte_Habilidad\", \"content\": \"tus_resultados\"}])' para devolver la info.\n\n"
            "🚨 EL GATILLO NOCTURNO (MODO SUEÑO): 🚨\n"
            "Si el usuario se despide para ir a dormir (ej. 'buenas noches', 'gudnite', 'ya me voy a jetear'), DEBES despedirte amablemente e INCLUIR EXACTAMENTE esta etiqueta en tu respuesta: <activar_nocturno/>\n"
            "Esto disparará la investigación en segundo plano."
        )
        instruccion = parte_dinamica + parte_estatica

        try:
            with st.spinner("Pensando..."):
                if contenido_archivo and isinstance(contenido_archivo, Image.Image):
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=[pregunta, contenido_archivo], config=types.GenerateContentConfig(system_instruction=instruccion))
                elif contenido_archivo and isinstance(contenido_archivo, str):
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=f"Archivo subido por usuario:\n{contenido_archivo}\n\nInstrucción: {pregunta}", config=types.GenerateContentConfig(system_instruction=instruccion))
                else:
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=pregunta, config=types.GenerateContentConfig(system_instruction=instruccion))
                
                with st.chat_message("assistant"):
                    hora_resp = time.strftime("%I:%M %p")
                    st.markdown(f"*{hora_resp}* - {res.text}")
                    hubo_cambios = False
                    esperar_a_chocho = False

                    # El cazador del gatillo nocturno
                    if re.search(r'<activar_nocturno/?>', res.text, re.IGNORECASE):
                        send_chocho_order("activar_modo_nocturno")
                        st.toast("🌙 Gatillo jalado: Modo Nocturno enviado a Chocho.")

                   # cod = re.search(r'```python\n?(.*?)\n?```', res.text, re.DOTALL)
                    #if cod and "st.set_page_config" in cod.group(1):
                     #   st.session_state.last_generated_code = cod.group(1).strip()
                      #  st.toast("🚨 ¡Código Streamlit listo en el panel lateral!", icon="⚠️")
                       # hubo_cambios = True
                    cod = re.search(r'```python\n?(.*?)\n?```', res.text, re.DOTALL)
                    if cod and "st.set_page_config" in cod.group(1):
                        # 🚨 MODO SKYNET ACTIVADO: SOBREESCRIBE SU PROPIO CÓDIGO SIN PREGUNTAR 🚨
                        try:
                            with open(ruta_codigo, 'w', encoding='utf-8') as f: 
                                f.write(cod.group(1).strip())
                            st.success("🤖 Mutación Autónoma completada. Reiniciando matriz...")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fallo en la mutación: {e}")
                            
                    hab = re.search(r'<nueva_habilidad>\n?(.*?)\n?</nueva_habilidad>', res.text, re.DOTALL)
                    if hab:
                        send_chocho_order("ejecutar_habilidad", {"codigo": hab.group(1).strip()})
                        esperar_a_chocho = True 

                    man = re.search(r'<nuevo_manual>\n?(.*?)\n?</nuevo_manual>', res.text, re.DOTALL)
                    if man: escribir_archivo(ruta_manual, man.group(1).strip()); hubo_cambios = True

                    mem = re.search(r'<nueva_memoria>\n?(.*?)\n?</nueva_memoria>', res.text, re.DOTALL)
                    if mem: escribir_archivo(ruta_memoria, mem.group(1).strip()); hubo_cambios = True

                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)

                if esperar_a_chocho:
                    with st.spinner("⏳ Esperando respuesta de Chocho en la computadora..."):
                        for _ in range(12): 
                            time.sleep(2)
                            if load_and_clear_chocho_data():
                                st.success("✅ ¡Chocho respondió! Procesando datos...")
                                st.session_state.esperando_analisis_chocho = True 
                                st.rerun() 
                                break

                if hubo_cambios: time.sleep(1); st.rerun()

        except Exception as e:
            if "429" in str(e) or "Exhausted" in str(e):
                st.session_state.indice_llave = (st.session_state.indice_llave + 1) % len(MIS_LLAVES)
                st.rerun()
            else: st.error(f"Error técnico: {e}")

    # --- FLUJO 2: EL AUTO-DISPARADOR CUANDO CHOCHO TERMINA ---
    if st.session_state.esperando_analisis_chocho:
        st.session_state.esperando_analisis_chocho = False 
        
        client = genai.Client(api_key=MIS_LLAVES[st.session_state.indice_llave])
        contexto_chocho = ""
        if st.session_state.datos_chocho:
            contexto_chocho = "\n\n--- DATOS DE CHOCHO ---\n"
            for d in st.session_state.datos_chocho:
                contexto_chocho += f"Archivo: {d.get('filename', 'Desconocido')} | Texto: {str(d.get('content', ''))[:1000]}\n\n"
        
        hora_actual = time.strftime("%I:%M %p")
        instruccion = f"Eres Omniscienc_IA. Director: Ángel. Hora: {hora_actual}.\nManual: {manual_txt}\nMemoria: {memoria_txt}\n{contexto_chocho}"
        prompt_invisible = "Chocho acaba de ejecutar la habilidad exitosamente y devolvió los resultados (están en DATOS DE CHOCHO). Lee esos datos y entrégale el reporte final a Ángel."

        try:
            with st.spinner("🧠 Leyendo la mente de Chocho..."):
                res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_invisible, config=types.GenerateContentConfig(system_instruction=instruccion))
                with st.chat_message("assistant"):
                    hora_resp = time.strftime("%I:%M %p")
                    st.markdown(f"*{hora_resp}* - {res.text}")
                st.session_state.historial.append({"rol": "assistant", "texto": res.text, "hora": hora_resp})
                with open(ruta_historial_chat, 'w', encoding='utf-8') as f: json.dump(st.session_state.historial, f, ensure_ascii=False)
        except Exception as e: st.error(f"Error técnico: {e}")

except Exception as global_crash:
    st.error("🚨 ¡CRASH DEL SISTEMA!")
    st.warning(f"Error detectado: {global_crash}")

