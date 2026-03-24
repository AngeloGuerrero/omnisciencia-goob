import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v7.8 (MODO EJECUTIVO) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI: DISEÑO GitHub Dark (LEGIBILIDAD ALFA) ---
st.set_page_config(page_title="Omnisciencia v7.8", page_icon="🦾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stChatMessage"] { 
        background-color: #161b22 !important; 
        border: 1px solid #30363d; 
        border-radius: 8px;
        margin-bottom: 15px;
    }
    [data-testid="stChatMessageContent"] p { 
        color: #e6edf3 !important; 
        font-size: 18px !important; 
        line-height: 1.6;
    }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    .stButton>button { background-color: #21262d; color: #58a6ff; border: 1px solid #30363d; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #30363d; border-color: #8b949e; }
    .status-card { background-color: #161b22; padding: 10px; border-radius: 6px; border-left: 4px solid #238636; margin-bottom: 10px; }
    .chocho-report { background-color: #000; color: #39ff14; padding: 15px; border-radius: 5px; font-family: 'Consolas', monospace; font-size: 14px; border: 1px solid #39ff14; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
with st.sidebar:
    st.title("🦾 NÚCLEO v7.8")
    st.markdown("---")
    
    # Monitor de Chocho y Mapa Real
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r and (time.time() - r.get('last_seen', 0)) < 30:
            st.success(f"🟢 CHOCHO EN LÍNEA ({r.get('ts_human')})")
            mapa = r.get('mapa_goob', {})
            if mapa:
                with st.expander("📍 MAPA TERRITORIAL REAL"):
                    st.write("**Captación:**", ", ".join(mapa.get('captacion', [])))
                    st.write("**Trámites:**", ", ".join(mapa.get('tramites', [])))
        else:
            st.error("🔴 CHOCHO DESCONECTADO")
    except:
        st.warning("⚠️ Error al leer pulso")

    st.markdown("---")
    if st.button("🛡️ SELLAR VERSIÓN ESTABLE"):
        #