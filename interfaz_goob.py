import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- LIBRERÍAS DEL CHALÁN (CLOUDBRIDGE) ---
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
except ImportError:
    st.error("Instalando dependencias de Google API...")

# --- IDENTIDAD SKYNET v5.2 ---
APP_ID = "omnisciencia-goob"
ruta_codigo = os.path.abspath(__file__)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        data = {"last_heartbeat": time.time(), "status": "ALIVE", "v": "5.2"}
        requests.put(f"{FIREBASE_URL}/status/skynet.json", json=data, timeout=3)
    except: pass

# --- EL CHALÁN WEB (OPERACIÓN NUBE) ---
def chalan_buscar_en_drive(termino):
    """Busca archivos en Google Drive usando la Service Account de Secrets."""
    try:
        if "google_drive" not in st.secrets:
            return "❌ Chalán: No detecto mis llaves en 'Secrets'. ¿Ya pegaste el JSON?"
        
        # Cargar credenciales desde el secreto
        info_json = json.loads(st.secrets["google_drive"]["service_account"])
        creds = service_account.Credentials.from_service_account_info(info_json)
        service = build('drive', 'v3', credentials=creds)
        
        # Ejecutar búsqueda
        query = f"name contains '{termino}' and trashed = false"
        results = service.files().list(
            q=query, pageSize=10, fields="files(id, name, webViewLink)"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return f"🔍 Chalán: Busqué '{termino}' en la nube pero no encontré nada, Director."
        
        reporte = f"📁 **Hallazgos en la Nube (Drive):**\n"
        for item in items:
            reporte += f"- **{item['name']}** ([Abrir en Drive]({item['webViewLink']}))\n"
        return reporte
    except Exception as e:
        return f"⚠️ Error del Chalán: {str(e)}"

# --- CHOCHO (OPERACIÓN LOCAL DISCO G:) ---
def enviar_orden_universal(comando, payload=None):
    try:
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        # Compatibilidad con Chochos viejos (enviar código directo)
        if payload and "codigo" in payload: data["codigo"] = payload["codigo"]
        requests.post(f"{FIREBASE_URL}/ordenes.json", json=data, timeout=5)
        return True
    except: return False

def leer_respuestas_locales():
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            requests.delete(url)
            return datos
    except: pass
    return None

# --- UI SETTINGS ---
st.set_page_config(page_title="Skynet v5.2", page_icon="🛰️", layout="wide")
enviar_latido()

if "esperando" not in st.session_state: st.session_state.esperando = False

# --- SIDEBAR: MONITOR DE NODOS ---
with st.sidebar:
    st.header("🛰️ Red de Nodos")
    
    # Nodo Nube
    st.subheader("☁️ Chalán Web")
    if "google_drive" in st.secrets:
        st.success("ONLINE (Acceso a Drive OK)")
    else:
        st.warning("CONFIGURACIÓN PENDIENTE")

    st.divider()
    
    # Nodo Local
    st.subheader("🏠 Chocho Local")
    try:
        r = requests.get(f"{FIREBASE_URL}/status/chocho.json", timeout=2)
        if r.status_code == 200 and r.json():
            beat = r.json()
            diff = time.time() - beat.get('last_seen', 0)
            if diff < 90: st.success(f"ONLINE (Hace {int(diff)}s)")
            else: st.warning(f"OFFLINE (Hace {int(diff)}s)")
        else: st.info("Esperando latido local...")
    except: st.error("Firebase desconectado")

    st.divider()
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        cmd = "import requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        enviar_orden_universal("ejecutar_habilidad", {"codigo": cmd})
        st.info("Orden de inyección enviada.")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_universal("save_stable_version", {"codigo": code})
        st.toast("Sello guardado en G:.")

# --- CHAT PRINCIPAL ---
st.title("🛰️ Skynet v5.2 (Omnipresencia Total)")
st.caption(f"Director: Ángel | Nodos Sincronizados | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []
for m in st.session_state.historial[-8:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Instrucción directa a la Matriz...")

if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    try:
        client = genai.Client(api_key=st.secrets["api_keys"]["llave_1"])
        
        sys_inst = (
            "ERES SKYNET v5.2 (Omnipresencia Total).\n"
            "TIENES DOS BRAZOS OPERATIVOS:\n"
            "1. EL CHALÁN WEB: Usa <chalan_web>termino</chalan_web> para buscar en la nube (Drive).\n"
            "2. CHOCHO LOCAL: Usa <nueva_habilidad>codigo_python</nueva_habilidad> para el disco G:.\n"
            "REGLA: Si el Director pide archivos generales, usa primero al Chalán."
        )

        with st.spinner("Procesando en la Red..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', contents=pregunta,
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Ejecutar Chalán (Nube)
                chal = re.search(r'<chalan_web>(.*?)</chalan_web>', res.text, re.DOTALL)
                if chal:
                    reporte = chalan_buscar_en_drive(chal.group(1).strip())
                    st.markdown(reporte)
                    st.session_state.historial.append({"rol": "assistant", "texto": reporte})
                
                # Ejecutar Chocho (Local)
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    code = hab.group(1).strip().replace("import os import", "import os\nimport")
                    enviar_orden_universal("ejecutar_habilidad", {"codigo": code})
                    st.session_state.esperando = True

        st.session_state.historial.append({"rol": "assistant", "texto": res.text})
    except Exception as e:
        st.error(f"Error en el núcleo: {e}")

# POLLING DE RESPUESTAS LOCALES
if st.session_state.esperando:
    resp = leer_respuestas_locales()
    if resp:
        st.session_state.esperando = False
        for r in resp:
            txt = f"🏠 **REPORTE LOCAL (Chocho):**\n{r.get('content')}"
            with st.chat_message("assistant"): st.markdown(txt)
            st.session_state.historial.append({"rol": "assistant", "texto": txt})
        st.rerun()
