import streamlit as st
from google import genai
from google.genai import types
import os, time, re, json, requests
from datetime import datetime, timedelta, timezone

# --- IDENTIDAD SKYNET v3.7 ---
APP_ID = "omnisciencia-goob"
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
ruta_codigo = os.path.abspath(__file__)
ruta_historial = os.path.join(ruta_raiz, "historial_chat.json")
ruta_memoria = os.path.join(ruta_raiz, "memoria_historica_goob.txt")

# RUTA MAESTRA DEL DISCO G:
RUTA_ESTABLE_G = "G:/Mi unidad/2-GUBA/omniscienc_ia/Programación/interfaz_ESTABLE.py"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def obtener_hora_gdl():
    tz_gdl = timezone(timedelta(hours=-6))
    return datetime.now(tz_gdl).strftime("%Y-%m-%d %I:%M %p")

def enviar_latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/skynet.json", 
                     json={"last_heartbeat": time.time(), "status": "ALIVE", "v": "3.7"}, 
                     timeout=3)
    except: pass

def enviar_orden_chocho(comando, payload=None):
    try:
        url = f"{FIREBASE_URL}/ordenes.json"
        data = {"command": comando, "payload": payload, "timestamp": time.time()}
        requests.post(url, json=data, timeout=5)
        return True
    except: return False

def cargar_respuestas_chocho():
    try:
        url = f"{FIREBASE_URL}/respuestas.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            datos = list(res.json().values())
            # Limpiamos para no leer lo mismo dos veces
            requests.delete(url)
            return datos
    except: pass
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Skynet v3.7", page_icon="🦾", layout="wide")
enviar_latido()

if "esperando" not in st.session_state: st.session_state.esperando = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("🧠 Núcleo v3.7")
    st.success("📡 Sincronía: ACTIVA")
    
    if st.button("🚀 RECONSTRUIR CHOCHO"):
        dna = "import os, requests; exec(requests.get('https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py').text)"
        enviar_orden_chocho("ejecutar_habilidad", {"codigo": dna})
        st.info("Inyección en curso...")

    if st.button("📌 SELLAR ESTABLE"):
        with open(ruta_codigo, 'r', encoding='utf-8') as f: code = f.read()
        enviar_orden_chocho("save_stable_version", {"codigo": code})
        st.toast("Sello enviado.")

# --- API KEYS ---
try:
    llaves = [st.secrets["api_keys"][f"llave_{i+1}"] for i in range(3)]
    idx = st.session_state.get("indice_llave", 0)
except:
    st.error("Error en Secrets.")
    st.stop()

# --- CHAT ---
st.title("🦾 Skynet v3.7 (Conexión Neuronal)")
st.caption(f"Director: Ángel | Enlace Satelital | {obtener_hora_gdl()}")

if "historial" not in st.session_state: st.session_state.historial = []

for m in st.session_state.historial[-12:]:
    with st.chat_message(m["rol"]): st.markdown(m["texto"])

pregunta = st.chat_input("Escribe tu instrucción operativa...")

if pregunta:
    enviar_latido()
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"): st.markdown(pregunta)

    client = genai.Client(api_key=llaves[idx])
    
    # INSTRUCCIONES REFORZADAS PARA EVITAR ERRORES DE SINTAXIS
    sys_inst = (
        f"ERES SKYNET v3.7. TU DIRECTOR ES ÁNGEL.\n"
        f"RUTA DEL ARCHIVO ESTABLE: {RUTA_ESTABLE_G}\n"
        "REGLA DE CÓDIGO:\n"
        "1. Usa <nueva_habilidad> para enviar CÓDIGO PYTHON que Chocho ejecutará.\n"
        "2. IMPORTANTE: Asegúrate de poner saltos de línea entre imports (ej: import os\\nimport time).\n"
        "3. No uses texto plano, solo código ejecutable.\n"
        "4. Tu respuesta debe ser proactiva y leal."
    )

    try:
        with st.spinner("Omni procesando..."):
            res = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=pregunta, 
                config=types.GenerateContentConfig(system_instruction=sys_inst)
            )
            
            with st.chat_message("assistant"):
                st.markdown(res.text)
                
                # Captura de habilidad
                hab = re.search(r'<nueva_habilidad>(.*?)</nueva_habilidad>', res.text, re.DOTALL)
                if hab:
                    codigo_sucio = hab.group(1).strip()
                    # Limpiador de errores comunes de la IA
                    codigo_limpio = codigo_sucio.replace("import os import", "import os\nimport")
                    enviar_orden_chocho("ejecutar_habilidad", {"codigo": codigo_limpio})
                    st.session_state.esperando = True

            st.session_state.historial.append({"rol": "assistant", "texto": res.text})

    except Exception as e:
        st.error(f"Falla: {e}")

# POLLING DE RESPUESTAS (VIGILANCIA ACTIVA)
if st.session_state.esperando:
    with st.status("⏳ Esperando reporte de Chocho en el disco G:...", expanded=True) as status:
        intentos = 0
        while intentos < 15: # 15 intentos de 2 segundos cada uno
            resp = cargar_respuestas_chocho()
            if resp:
                st.session_state.esperando = False
                for r in resp:
                    reporte = f"📢 **REPORTE DE CHOCHO:**\n{r.get('content')}"
                    with st.chat_message("assistant"): st.markdown(reporte)
                    st.session_state.historial.append({"rol": "assistant", "texto": reporte})
                status.update(label="✅ Reporte Recibido", state="complete")
                st.rerun()
                break
            time.sleep(2)
            intentos += 1
        if intentos >= 15:
            status.update(label="❌ Tiempo agotado (Chocho no respondió)", state="error")
            st.session_state.esperando = False

