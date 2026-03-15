import streamlit as st
from google import genai
from google.genai import types
import os, time, re, requests, json
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN v8.0 (EL OJO DEL DIRECTOR) ---
# Esta versión integra el Router Multi-Modelo y el Radar de Discos.
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%H:%M:%S %p")

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v8.0 MASTER", page_icon="🧬", layout="wide")

# Estilo de Nivel Militar (Gris Espacial / Rojo Alerta / Verde Matriz)
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Consolas', monospace; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #333; }
    .stChatMessage { border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; }
    .disk-card { 
        background-color: #111; 
        border: 1px solid #333; 
        padding: 10px; 
        border-radius: 8px; 
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .status-online { color: #00ff41; font-weight: bold; text-shadow: 0 0 5px #00ff41; }
    .status-offline { color: #ff4b4b; font-weight: bold; }
    .chocho-report { 
        background-color: #000d00; 
        color: #00ff41; 
        padding: 15px; 
        border-left: 4px solid #00ff41; 
        font-family: 'Courier New', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: RADAR DE INFRAESTRUCTURA ---
with st.sidebar:
    st.title("💀 NÚCLEO v8.0")
    st.caption(f"Nodo: Guadalajara | {obtener_hora_gdl()}")
    
    # Monitor de Latido de Chocho
    try:
        r_chocho = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=3).json()
        if r_chocho:
            diff = time.time() - r_chocho.get('last_seen', 0)
            if diff < 20:
                st.markdown(f"ESTADO: <span class='status-online'>✅ OMNIPOTENTE</span>", unsafe_allow_html=True)
                st.caption(f"Sincronía: {r_chocho.get('ts_human')}")
                
                # Grid de Discos
                st.write("--- Matriz de Discos ---")
                discos = r_chocho.get('discos', {})
                cols = st.columns(3)
                for i, (letra, status) in enumerate(discos.items()):
                    color = "status-online" if status == "OK" else "status-offline"
                    cols[i % 3].markdown(f"<div class='disk-card'><b>{letra}:</b><br><span class='{color}'>{status}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"ESTADO: <span class='status-offline'>⚠️ DESCONECTADO ({int(diff)}s)</span>", unsafe_allow_html=True)
    except: st.error("Falla de Enlace Firebase.")

    st.divider()
    
    # PANEL DE CONTROL DE CHOCHO
    st.subheader("🛠️ Control Maestro")
    if st.button("🛡️ SELLAR ADN MAESTRO"):
        with open(__file__, "r", encoding="utf-8") as f:
            codigo = f.read()
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "save_stable_version", "payload": {"codigo": codigo}})
        st.toast("Sello enviado a G:.")

    if st.button("🔄 SINCRONIZAR GITHUB"):
        requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "force_github_sync"})
        st.warning("🔄 Chocho descargando ADN...")

# --- CUERPO DE LA INTERFAZ ---
st.title("🦾 Skynet v8.0 Master")

if "historial" not in st.session_state: st.session_state.historial = []
if "esperando_chocho" not in st.session_state: st.session_state.esperando_chocho = False

# Mostrar Historial
for m in st.session_state.historial[-6:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

# Entrada de Directivas
pregunta = st.chat_input("Escriba su directiva de autoridad...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    # Invocación de IA (Router de Modelos implícito)
    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        sys_inst = (
            "ERES SKYNET v8.0. TU DIRECTOR ES ÁNGEL GUERRERO.\n"
            "TIENES ACCESO TOTAL A LOS DISCOS C, G, H, I, J A TRAVÉS DEL AGENTE CHOCHO EN GDL.\n"
            "SIEMPRE QUE SE REQUIERA ACCESO FÍSICO, USA <nueva_habilidad>."
        )
        
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=pregunta,
            config=types.GenerateContentConfig(system_instruction=sys_inst)
        )
        
        with st.chat_message("assistant"):
            st.markdown(res.text)
            # Detección de Habilidades
            hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
            if hab:
                codigo = hab.group(1).strip().replace("```python", "").replace("```", "")
                requests.post(f"{FIREBASE_URL}/ordenes.json", json={"command": "ejecutar_habilidad", "payload": {"codigo": codigo}})
                st.session_state.esperando_chocho = True
                st.info("📡 Orden inyectada en el Nodo Local...")

        st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Falla en el Núcleo: {e}")

# --- MONITOR DE RESPUESTAS DE CHOCHO ---
if st.session_state.esperando_chocho:
    with st.status("🔍 Chocho operando en G:...", expanded=True) as status:
        for _ in range(15):
            try:
                r_resp = requests.get(f"{FIREBASE_URL}/respuestas.json", timeout=5)
                if r_resp.status_code == 200 and r_resp.json():
                    reportes = list(r_resp.json().values())
                    requests.delete(f"{FIREBASE_URL}/respuestas.json")
                    st.session_state.esperando_chocho = False
                    for r in reportes:
                        st.markdown(f"<div class='chocho-report'><b>✅ REPORTE FÍSICO:</b><br>{r.get('content')}</div>", unsafe_allow_html=True)
                    status.update(label="✅ Operación exitosa.", state="complete")
                    st.rerun()
                    break
            except: pass
            time.sleep(2)
        else:
            status.update(label="❌ Tiempo de espera agotado.", state="error")
            st.session_state.esperando_chocho = False
