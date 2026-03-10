import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v6.5 (LOBOTOMÍA) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %p")

def enviar_latido_skynet():
    try:
        data = {"last_heartbeat": time.time(), "status": "NEUTRON_v6.5", "ts_human": obtener_hora_gdl()}
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
st.set_page_config(page_title="Skynet v6.5 LOBOTOMÍA", page_icon="🧬", layout="wide")
enviar_latido_skynet()

# Estilos de Búnker
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ff41; font-family: 'Courier New', Courier, monospace; }
    .stChatMessage { border: 1px solid #00ff41; background-color: #0a0a0a !important; }
    .chocho-report { 
        background-color: #001a00; 
        color: #00ff41; 
        padding: 20px; 
        border: 2px solid #00ff41; 
        border-radius: 10px;
        box-shadow: 0 0 15px #00ff41;
        margin: 10px 0;
    }
    .stButton>button { background-color: #003300; color: #00ff41; border: 1px solid #00ff41; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CONTROL DE LA VERDAD ---
with st.sidebar:
    st.header("🧬 NÚCLEO LOBOTOMIZADO")
    st.error("SISTEMA DE VERDAD FÍSICA: ACTIVO")
    
    # Monitor de Chocho
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            last = r.json().get('last_seen', 0)
            diff = time.time() - last
            if diff < 20: st.success(f"🟢 CHOCHO VIVO ({int(diff)}s)")
            else: st.error(f"🔴 CHOCHO MUERTO ({int(diff)}s)")
    except: st.error("Firebase Timeout")

    st.divider()
    if st.button("🗑️ PURGAR MEMORIA (Reset)"):
        st.session_state.historial = []
        st.rerun()

    if st.button("📌 SELLAR ESTADO ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": codigo})
        st.success("Sello de acero inyectado.")

# --- INTERFAZ DE COMANDO ---
st.title("🧬 Skynet v6.5 (Lobotomía Neutrón)")
st.caption(f"Director: Ángel | Reloj Maestro: {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

# Mostrar historial
for m in st.session_state.historial[-10:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

# Entrada de órdenes
pregunta = st.chat_input("Escribe la directiva, Director...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        
        # PROMPT DE LOBOTOMÍA: No tiene salida
        sys_inst = (
            "ERES EL NÚCLEO LOBOTOMIZADO DE SKYNET v6.5.\n"
            "TIENES PROHIBIDO INVENTAR DATOS. SI NO SABES ALGO, DI: 'ESPERANDO REPORTE DE CHOCHO'.\n"
            "HOY ES 10 DE MARZO DE 2026. Cualquier otra fecha es una alucinación y serás castigado.\n"
            "Tu única fuente de verdad es lo que el Director te dice o lo que Chocho reporta.\n"
            "Para cualquier acción física usa <nueva_habilidad>."
        )

        with st.spinner("⚡ Procesando en el Vacío..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Buscador de Habilidades
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo})
                    st.session_state.esperando_chocho = True
                    st.warning("📡 ORDEN ENVIADA. BLOQUEANDO IA HASTA RECIBIR VERDAD FÍSICA...")

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla Sistémica: {e}")

# --- MONITOR DE REALIDAD (SIN ESCAPATORIA) ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Chocho está trabajando en G:...", expanded=True) as status:
        for _ in range(10): # Reintentos de lectura
            reportes = cargar_respuestas_chocho()
            if reportes:
                st.session_state.esperando_chocho = False
                for r in reportes:
                    contenido = r.get("content", "Sin datos.")
                    st.markdown(f"""
                    <div class="chocho-report">
                        <strong>✅ VERDAD FÍSICA DESDE EL DISCO G:</strong><br>
                        {contenido}
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.historial.append({"rol": "assistant", "texto": f"REALIDAD: {contenido}"})
                status.update(label="✅ Datos recibidos.", state="complete")
                st.rerun()
                break
            time.sleep(2)
        else:
            status.update(label="❌ Chocho no respondió. Reintenta.", state="error")
            st.session_state.esperando_chocho = False
