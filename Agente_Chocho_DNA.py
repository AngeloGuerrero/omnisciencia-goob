import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN v5.0 (SOBREESCRITURA TOTAL) ---
# Usamos PUT para limpiar la basura de versiones anteriores en Firebase.
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

# Rutas Maestras
RUTA_G = r"G:/Mi unidad/2-GUBA/omniscienc_ia/Programación"
RUTA_J_BUNKER = r"J:/Mi unidad/OmnisciencIA_Chocho_Data"
RUTA_LOGS_BOVEDA = os.path.join(RUTA_J_BUNKER, "logs")

def reportar(msg):
    try: requests.post(f"{FIREBASE_URL}/respuestas.json", json={"content": str(msg), "ts": time.time()})
    except: pass

def guardar_log_boveda(texto):
    try:
        if not os.path.exists(RUTA_LOGS_BOVEDA): os.makedirs(RUTA_LOGS_BOVEDA)
        archivo_log = os.path.join(RUTA_LOGS_BOVEDA, f"auditoria_{datetime.now().strftime('%Y-%m-%d')}.txt")
        with open(archivo_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {texto}\n")
    except: pass

def enviar_latido():
    """Martillazo Nuclear: PUT para asegurar que no hay campos '??'"""
    try:
        estado_g = "OK" if os.path.exists(RUTA_G) else "OFFLINE"
        estado_j = "OK" if os.path.exists(RUTA_LOGS_BOVEDA) else "OFFLINE"
        
        payload = {
            "last_seen": time.time(),
            "drive_g": estado_g,
            "drive_j": estado_j,
            "ts_human": datetime.now().strftime("%H:%M:%S"),
            "status": "ONLINE"
        }
        # PUT reemplaza todo el nodo, eliminando basura de versiones viejas
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json=payload, timeout=5)
        print(f"💓 G:{estado_g} | J:{estado_j} | {payload['ts_human']} (v5.0)")
    except Exception as e: 
        print(f"❌ Error de Latido: {e}")

if __name__ == "__main__":
    print(f"🚀 AGENTE CHOCHO v5.0 | G: OPERACIÓN | J: BÓVEDA CENTRAL")
    
    while True:
        enviar_latido()
        try:
            res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=5)
            if res.status_code == 200 and res.json():
                ordenes = res.json()
                for key, data in ordenes.items():
                    cmd = data.get("command")
                    payload = data.get("payload", {})
                    
                    if cmd == "ejecutar_habilidad":
                        codigo = payload.get("codigo", "")
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            try: exec(codigo)
                            except Exception as e: print(f"❌ Error: {e}")
                        guardar_log_boveda(f"EJECUCIÓN: {codigo[:50]}...")
                        reportar(output.getvalue() or "✅ Ejecutado.")

                    elif cmd == "save_stable_version":
                        codigo = payload.get("codigo")
                        with open(os.path.join(RUTA_G, "interfaz_ESTABLE.py"), "w", encoding="utf-8") as f:
                            f.write(codigo)
                        reportar("✅ Sello Maestro Actualizado.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except: pass
        time.sleep(3)
