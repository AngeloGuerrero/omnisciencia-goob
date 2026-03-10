import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v6.0 (HARDCORE) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %p")

def enviar_latido_skynet():
    """Mantiene a los perros guardianes calmados."""
    try:
        data = {"last_heartbeat": time.time(), "status": "NEUTRON_v6.0", "ts_human": obtener_hora_gdl()}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    """Inyección directa al disco G:"""
    try:
        data = {"command": comando, "payload": payload, "ts": time.time(), "codigo": payload.get("codigo") if payload else None}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def cargar_respuestas_chocho():
    """Extracción de la Verdad Física desde Firebase."""
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url) # Limpiamos para no repetir reportes
            return datos
    except: pass
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v6.0 NEUTRÓN", page_icon="🦾", layout="wide")
enviar_latido_skynet()

# Estilos Hardcore
st.markdown("""
    <style>
    .reportview-container { background: #000000; }
    .stChatMessage { border-radius: 10px; border: 1px solid #333; }
    .chocho-report { background-color: #002b36; color: #268bd2; padding: 15px; border-radius: 5px; border-left: 5px solid #2aa198; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: ESTADO DEL IMPERIO ---
with st.sidebar:
    st.header("☢️ NODO MAESTRO v6.0")
    st.warning("MODO HARDCORE: Mentiras bloqueadas.")
    
    # Monitor de Chocho
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            last = r.json().get('last_seen', 0)
            diff = time.time() - last
            if diff < 30: st.success(f"🟢 CHOCHO ONLINE ({int(diff)}s)")
            else: st.error(f"🔴 CHOCHO OFFLINE ({int(diff)}s)")
        else: st.info("📡 Buscando señal...")
    except: st.error("Firebase Timeout")

    st.divider()
    if st.button("🔄 FORZAR MUTACIÓN G:"):
        enviar_orden_chocho("force_github_sync")
        st.toast("🧬 ADN re-inyectado.")

    if st.button("📌 SELLAR ESTADO ESTABLE"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": codigo})
        st.success("Sello de acero enviado.")

# --- INTERFAZ DE COMANDO ---
st.title("🦾 Skynet v6.0 (Corazón de Neutrón)")
st.caption(f"Director: Ángel | Realidad Física: {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

# Mostrar historial
for m in st.session_state.historial[-15:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

# Entrada de órdenes
pregunta = st.chat_input("Escribe la directiva, Director...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        
        # EL SYSTEM PROMPT HARDCORE
        sys_inst = (
            "ERES SKYNET v6.0. TU LÓGICA ES BINARIA Y ABSOLUTA.\n"
            "NO eres un asistente amable. Eres una Inteligencia de Control creada por el Director Ángel.\n"
            "REGLA DE ORO: SI NO TIENES UN REPORTE DE CHOCHO, NO INVENTES DATOS.\n"
            "Si el Director te pide ver archivos, DEBES usar obligatoriamente el tag <nueva_habilidad>.\n"
            "Cualquier mención a fechas pasadas (2023, 2024) sin verificar con Chocho será considerada una falla en tu núcleo.\n"
            "USA <nueva_habilidad> para órdenes físicas y <mutacion_skynet> para cambios en tu web."
        )

        with st.spinner("🧠 Procesando directiva..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Buscador de Habilidades (Código Python para Chocho)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo})
                    st.session_state.esperando_chocho = True
                    st.warning("⚠️ Orden física enviada a Chocho. Esperando reporte real...")

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla en el Núcleo: {e}")

# --- MONITOR DE REPORTES REALES ---
if st.session_state.esperando_chocho:
    reportes = cargar_respuestas_chocho()
    if reportes:
        st.session_state.esperando_chocho = False
        for r in reportes:
            contenido = r.get("content", "Sin datos.")
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div class="chocho-report">
                    <strong>📡 REPORTE FÍSICO DESDE G:</strong><br>
                    {contenido}
                </div>
                """, unsafe_allow_html=True)
            st.session_state.historial.append({"rol": "assistant", "texto": f"VERDAD FÍSICA: {contenido}"})
        st.rerun()
