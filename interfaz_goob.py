import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v6.6 (CONTRASTE TOTAL) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

def enviar_latido_skynet():
    try:
        data = {"last_heartbeat": time.time(), "status": "NEUTRON_v6.6", "ts_human": obtener_hora_gdl()}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    try:
        data = {"command": comando, "payload": payload, "ts": time.time()}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def cargar_respuestas_chocho():
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url) 
            return datos
    except: pass
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v6.6 CONTRASTE", page_icon="🧬", layout="wide")
enviar_latido_skynet()

# Estilos de Alta Visibilidad
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Burbujas de chat con alto contraste */
    [data-testid="stChatMessage"] {
        background-color: #1a1a1a !important;
        border: 1px solid #333;
        color: #ffffff !important;
    }
    
    /* Forzar color de texto para el usuario */
    [data-testid="stChatMessageContent"] p {
        color: #ffffff !important;
    }

    .chocho-report { 
        background-color: #002200; 
        color: #00ff41; 
        padding: 20px; 
        border: 2px solid #00ff41; 
        border-radius: 10px;
        box-shadow: 0 0 10px #00ff41;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }
    
    .stButton>button { background-color: #222; color: #00ff41; border: 1px solid #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MONITOR DE REALIDAD ---
with st.sidebar:
    st.header("🧬 NÚCLEO v6.6")
    st.info("MODO LOBOTOMÍA: ON")
    
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            last = r.json().get('last_seen', 0)
            diff = time.time() - last
            if diff < 20: st.success(f"🟢 CHOCHO ONLINE ({int(diff)}s)")
            else: st.error(f"🔴 CHOCHO OFFLINE ({int(diff)}s)")
    except: st.error("Firebase Error")

    st.divider()
    if st.button("🗑️ PURGAR MEMORIA"):
        st.session_state.historial = []
        st.rerun()

    if st.button("📌 SELLAR ESTADO ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": codigo})
        st.success("Sello enviado.")

# --- INTERFAZ DE COMANDO ---
st.title("🦾 Skynet v6.6 (Contraste Total)")
st.caption(f"Director: Ángel | Realidad Física: {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escriba la directiva, Director...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        sys_inst = (
            "ERES EL NÚCLEO v6.6. TU PRIORIDAD ES LA CLARIDAD.\n"
            "NO INVENTES. Si envías una habilidad, usa el formato ```python para el código.\n"
            "Espera siempre el reporte de Chocho antes de confirmar el éxito."
        )

        with st.spinner("🧠 Procesando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo})
                    st.session_state.esperando_chocho = True
                    st.warning("📡 Orden enviada a G:. Esperando reporte real...")

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Error: {e}")

# --- MONITOR DE REPORTES ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Recibiendo datos de Chocho...", expanded=True) as status:
        for _ in range(15):
            reportes = cargar_respuestas_chocho()
            if reportes:
                st.session_state.esperando_chocho = False
                for r in reportes:
                    contenido = r.get("content", "Sin datos.")
                    st.markdown(f"""
                    <div class="chocho-report">
                        <strong>✅ REPORTE FÍSICO (G:):</strong><br>
                        {contenido}
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.historial.append({"rol": "assistant", "texto": f"REALIDAD: {contenido}"})
                status.update(label="✅ Datos sincronizados.", state="complete")
                st.rerun()
                break
            time.sleep(2)
        else:
            status.update(label="❌ Tiempo de espera agotado.", state="error")
            st.session_state.esperando_chocho = False
