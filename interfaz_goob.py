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
import json
import requests
from PIL import Image
import io
from datetime import datetime, timedelta, timezone

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

def obtener_hora_gdl():
    """Calcula la hora exacta de Guadalajara (UTC-6) sin importar dónde esté el servidor"""
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
