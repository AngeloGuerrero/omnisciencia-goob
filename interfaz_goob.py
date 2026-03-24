import streamlit as st
import google.generativeai as genai # Librería estable
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v8.0 (ESTABILIDAD LEGACY) ---
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI: DISEÑO GitHub Dark ---
st.set_page_config(page_title="Omnisciencia v8.0", page_icon="🦾", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stChatMessage"] { background-color: #161b22 !important; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 15px; }
    [data-testid="stChatMessageContent"] p { color: #e6edf3 !important; font-size: 18px !important; line-height: 1.6; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
    .stButton>button { background-color: #21262d; color: #58a6ff; border: 1px solid #30363d; width: 100%; font-weight: bold; }
    .chocho-report { background-color: #000; color: #39ff14; padding: 15px; border-radius: 5px; font-family: 'Consolas', monospace; font-size: 14px; border: 1px solid #39ff14; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🦾 NÚCLEO v8.0")
    st.markdown("---")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r and (time.time() - r.get('last_seen', 0)) < 60:
            st.success(f"🟢 CHOCHO VIVO ({r.get('ts_human')})")
            mapa = r.get('mapa_goob', {})
            if mapa:
                with st.expander("📍 MAPA TERRITORIAL", expanded=True):
                    st.write("**Captación:**", ", ".join(mapa.get('captacion', [])))
                    st.write("**Trámites:**", ", ".join(mapa.get('tramites', [])))
        else:
            st.error("🔴 CHOCHO OFFLINE")
    except:
        st.warning("⚠️ Error Firebase")

# --- LÓGICA DE ROTACIÓN (LIBRERÍA ESTABLE) ---
def llamar_ia_v8(instruccion, prompt):
    llaves = ["llave_1", "llave_2", "llave_3"]
    for alias in llaves:
        try:
            # Verificamos si la llave existe en secrets
            if alias in st.secrets.get("api_keys", {}):
                key = st.secrets["api_keys"][alias]
                genai.configure(api_key=key)
                # Modelo con nomenclatura estable
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction=instruccion
                )
                res = model.generate_content(prompt)
                return res.text, alias
        except Exception as e:
            continue
    return "❌ TODAS LAS LLAVES FALLARON. Revisa tus Secrets en Streamlit.", "ERROR"

# --- CHAT ---
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
        r_m = requests.get(f"{FIREBASE_URL}/status/chocho.json").json()
        ctx = json.dumps(r_m.get('mapa_goob', {}))
    except:
        ctx = "{}"

    sys_inst = f"ERES OMNISCIENCIA. DIRECTOR: ÁNGEL. MAPA REAL: {ctx}. No inventes rutas."
    
    with st.spinner("Conectando con el NÚCLEO..."):
        respuesta, llave = llamar_ia_v8(sys_inst, pregunta)

    with st.chat_message("assistant"):
        st.markdown(respuesta)
        if "❌" not in respuesta:
            st.caption(f"📡 Llave activa: {llave}")
        
        hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', respuesta, re.DOTALL)
        if hab:
            codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
            requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
            st.session_state.esperando = True

    st.session_state.historial.append({"rol": "assistant", "texto": respuesta})

# Monitor Chocho
if st.session_state.esperando:
    with st.status("🛠️ Chocho operando...", expanded=True) as s:
        for _ in range(15):
            try:
                r_res = requests.get(f"{FIREBASE_URL}/respuestas.json").json()
                if r_res:
                    resp = list(r_res.values())[0]
                    st.markdown(f'<div class="chocho-report"><strong>REPORTE LOCAL:</strong><br>{resp.get("content")}</div>', unsafe_allow_html=True)
                    requests.delete(f"{FIREBASE_URL}/respuestas.json")
                    st.session_state.esperando = False
                    s.update(label="✅ Finalizado", state="complete")
                    break
            except: pass
            time.sleep(2)
        else:
            st.session_state.esperando = False
            s.update(label="⚠️ Sin respuesta", state="error")