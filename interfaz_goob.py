import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v7.9 (MODO OPERACIONES) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI: DISEÑO GitHub Dark ---
st.set_page_config(page_title="Omnisciencia v7.9", page_icon="🦾", layout="wide")

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
    .chocho-report { background-color: #000; color: #39ff14; padding: 15px; border-radius: 5px; font-family: 'Consolas', monospace; font-size: 14px; border: 1px solid #39ff14; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR OPERATIVO ---
with st.sidebar:
    st.title("🦾 NÚCLEO v7.9")
    st.markdown("---")
    
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r and (time.time() - r.get('last_seen', 0)) < 45:
            st.success(f"🟢 CHOCHO EN LÍNEA ({r.get('ts_human')})")
            mapa = r.get('mapa_goob', {})
            if mapa:
                with st.expander("📍 MAPA TERRITORIAL REAL", expanded=True):
                    st.write("**Captación:**", ", ".join(mapa.get('captacion', [])))
                    st.write("**Trámites:**", ", ".join(mapa.get('tramites', [])))
        else:
            st.error("🔴 CHOCHO DESCONECTADO")
    except:
        st.warning("⚠️ Error de pulso")

    st.markdown("---")
    if st.button("🛡️ SELLAR VERSIÓN ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable", "payload": {"codigo": codigo}})
        st.info("Sello enviado.")

# --- CHAT PRINCIPAL ---
st.title("Gestión Omnisciencia GOOB")
st.caption(f"Director: Ángel Guerrero | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando" not in st.session_state: st.session_state.esperando = False

for m in st.session_state.historial[-6:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escriba su instrucción...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        r_mapa = requests.get(f"{FIREBASE_URL}/status/chocho.json").json()
        contexto_real = json.dumps(r_mapa.get('mapa_goob', {}))
    except:
        contexto_real = "{}"

    sys_inst = (
        f"ERES OMNISCIENCIA. DIRECTOR: ÁNGEL. MAPA REAL: {contexto_real}. "
        "Usa este mapa para dar opciones reales. No inventes rutas."
    )
    
    client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
    res = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=[{"role": "user", "parts": [{"text": pregunta}]}],
        config=types.GenerateContentConfig(system_instruction=sys_inst)
    )
    
    with st.chat_message("assistant"):
        st.markdown(res.text)
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
        if hab:
            codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
            st.session_state.esperando = True

    st.session_state.historial.append({"rol": "assistant", "texto": res.text})

if st.session_state.esperando:
    with st.status("🛠️ Chocho operando...", expanded=True) as s:
        for _ in range(15):
            r_res = requests.get(f"{FIREBASE_URL}/respuestas.json").json()
            if r_res:
                resp = list(r_res.values())[0]
                st.markdown(f'<div class="chocho-report">{resp.get("content")}</div>', unsafe_allow_html=True)
                requests.delete(f"{FIREBASE_URL}/respuestas.json")
                st.session_state.esperando = False
                s.update(label="✅ Finalizado", state="complete")
                break
            time.sleep(2)
        else:
            st.session_state.esperando = False
            s.update(label="❌ Timeout", state="error")