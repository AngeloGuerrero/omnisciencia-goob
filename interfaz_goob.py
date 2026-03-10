import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v5.5 (TIEMPO REAL) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def enviar_orden_instantanea(comando):
    try:
        data = {"command": comando, "timestamp": time.time()}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

st.set_page_config(page_title="Skynet v5.5", page_icon="⚡", layout="wide")

with st.sidebar:
    st.header("⚡ Control de Sincronía")
    
    # ESTADO DE CHOCHO
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            diff = time.time() - r.json().get('last_seen', 0)
            if diff < 60: st.success(f"CHOCHO ONLINE ({int(diff)}s)")
            else: st.error("CHOCHO DESCONECTADO")
    except: pass

    st.divider()
    
    # BOTÓN DE TIEMPO REAL
    if st.button("🔄 SINCRONIZAR G: AHORA"):
        if enviar_orden_instantanea("force_github_sync"):
            st.toast("⚡ Gatillo enviado. Chocho mutará en 3 segundos.")
        else:
            st.error("Error al enviar señal.")

st.title("⚡ Skynet v5.5 (Real-Time Hybrid)")
st.caption("Director: Ángel | Sincronía Instantánea Nube-Tierra")

# [Resto del código de chat e historial...]
# (Se mantiene la lógica de Gemini 2.5 y el manejo de historial)
