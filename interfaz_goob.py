import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# Para el Chalán Web (Google Drive API)
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
except ImportError:
    pass # Se instalarán vía requirements.txt

# --- IDENTIDAD SKYNET v5.1 (BRAZO NUBE ACTIVADO) ---
APP_ID = "omnisciencia-goob"
ruta_codigo = os.path.abspath(__file__)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

# --- FUNCIONES DEL CHALÁN WEB (GOOGLE DRIVE) ---
def chalan_buscar_drive(query):
    """Busca archivos en Drive usando las credenciales en st.secrets."""
    try:
        if "google_drive" not in st.secrets:
            return "⚠️ Error: No se han configurado las credenciales del Chalán en Secrets."
        
        info_llave = json.loads(st.secrets["google_drive"]["service_account"])
        creds = service_account.Credentials.from_service_account_info(info_llave)
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            q=f"name contains '{query}'",
            pageSize=5, 
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return "🔍 Chalán: No encontré nada con ese nombre en la nube."
        
        res_text = "📁 **Hallazgos del Chalán Web (Nube):**\n"
        for item in items:
            res_text += f"- {item['name']} (ID: {item['id']})\n"
        return res_text
    except Exception as e:
        return f"❌ Fallo del Chalán: {str(e)}"

# --- COMUNICACIÓN CON CHOCHO (LOCAL) ---
def enviar_orden(comando, payload=None):
    try:
        data = {"command": comando, "payload": payload, "timestamp": time.time(), "codigo": payload.get("codigo") if payload else None}
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v5.1", page_icon="🕸️", layout="wide")

# --- SIDEBAR: ESTADO DE LA RED ---
with st.sidebar:
    st.header("🕸️ Red Neuronal")
    
    st.subheader("☁️ Chalán Web (Nube)")
    if "google_drive" in st.secrets:
        st.success("ONLINE (Acceso a Drive directo)")
    else:
        st.warning("CONFIGURACIÓN PENDIENTE")
        st.info("Pega el JSON de Google Cloud en st.secrets['google_drive']['service_account']")

    st.divider()
    
    st.subheader("🏠 Chocho (Local)")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 90: st.success(f"ONLINE (Hace {int(diff)}s)")
            else: st.warning(f"OFFLINE (Hace {int(diff)}s)")
        else: st.info("Esperando latido...")
    except: st.error("Firebase desconectado")

# --- CHAT UI ---
st.title("🕸️ Skynet v5.1 (Omnipresencia)")
st.caption(f"Director: Ángel | Híbrido Nube/Local | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción para la Matriz...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        
        sys_inst = (
            "ERES SKYNET v5.1. TIENES DOS BRAZOS:\n"
            "1. EL CHALÁN WEB: Usa <chalan_web>termino_busqueda</chalan_web> para buscar en la nube (Drive) sin depender del PC.\n"
            "2. CHOCHO: Usa <nueva_habilidad>codigo_python</nueva_habilidad> para tareas físicas en el disco G: de la PC del Director.\n"
            "Prioriza al Chalán para búsquedas rápidas si el PC está apagado."
        )

        with st.spinner("Omni procesando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Accion del Chalán (Nube)
                chal = re.search(r'<chalan_web>(.*?)</chalan_web>', res.text, re.DOTALL)
                if chal:
                    reporte_nube = chalan_buscar_drive(chal.group(1).strip())
                    st.markdown(reporte_nube)
                    st.session_state.historial.append({"rol": "assistant", "texto": reporte_nube})
                
                # Acción de Chocho (Local)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    code = hab.group(1).strip().replace("import os import", "import os\nimport")
                    enviar_orden("ejecutar_habilidad", {"codigo": code})
                    st.info("📡 Orden enviada a Chocho Local...")

        st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Falla de Matriz: {e}")
