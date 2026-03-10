import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN v4.9 (BÓVEDA CENTRALIZADA - SINCRONÍA ATÓMICA) ---
APP_ID = "omnisciencia-goob"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

# Rutas Maestras según Capturas image_347de0.png e image_3482b4.png
RUTA_G = r"G:/Mi unidad/2-GUBA/omniscienc_ia/Programación"
RUTA_J_BUNKER = r"J:/Mi unidad/OmnisciencIA_Chocho_Data"
RUTA_LOGS_BOVEDA = os.path.join(RUTA_J_BUNKER, "logs")

def reportar(msg):
    try: requests.post(f"{FIREBASE_URL}/respuestas.json", json={"content": str(msg), "ts": time.time()})
    except: pass

def guardar_log_boveda(texto):
    """Escribe la auditoría directamente en la carpeta 'logs' del disco J:"""
    try:
        if not os.path.exists(RUTA_LOGS_BOVEDA): os.makedirs(RUTA_LOGS_BOVEDA)
        fecha = datetime.now().strftime("%Y-%m-%d")
        archivo_log = os.path.join(RUTA_LOGS_BOVEDA, f"auditoria_{fecha}.txt")
        with open(archivo_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {texto}\n")
    except Exception as e: print(f"Error Log J: {e}")

def enviar_latido():
    """Envía un pulso de alta visibilidad para la interfaz web"""
    try:
        # Verificamos existencia física de rutas
        estado_g = "OK" if os.path.exists(RUTA_G) else "OFFLINE"
        estado_j = "OK" if os.path.exists(RUTA_LOGS_BOVEDA) else "OFFLINE"
        
        payload = {
            "last_seen": time.time(),
            "drive_g": estado_g,
            "drive_j": estado_j,
            "ts_human": datetime.now().strftime("%H:%M:%S"),
            "status": "ONLINE",
            "version": "v4.9"
        }
        # Usamos patch para no borrar otras ramas de status si existieran
        requests.patch(f"{FIREBASE_URL}/status/chocho.json", json=payload, timeout=5)
        print(f"💓 G:{estado_g} | J:{estado_j} | {payload['ts_human']}")
    except Exception as e: 
        print(f"❌ Error de Latido: {e}")

if __name__ == "__main__":
    print(f"🚀 AGENTE CHOCHO v4.9 | G: OPERACIÓN | J: BÓVEDA CENTRAL")
    if not os.path.exists(RUTA_LOGS_BOVEDA): 
        print(f"⚠️ Alerta: No se detecta la carpeta de logs en J: {RUTA_LOGS_BOVEDA}")
    
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
                            try: 
                                exec(codigo)
                                guardar_log_boveda(f"EJECUCIÓN: {codigo[:120]}...")
                            except Exception as e: 
                                err = f"FALLO: {str(e)}"
                                print(err)
                                guardar_log_boveda(err)
                        reportar(output.getvalue() or "✅ Orden procesada.")

                    elif cmd == "save_stable_version":
                        codigo = payload.get("codigo")
                        path_estable = os.path.join(RUTA_G, "interfaz_ESTABLE.py")
                        with open(path_estable, "w", encoding="utf-8") as f:
                            f.write(codigo)
                        guardar_log_boveda("SELLO ESTABLE CREADO EN DISCO G:")
                        reportar("✅ Sello Maestro Actualizado.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except Exception as e: print(f"⚠️ Error de red: {e}")
        time.sleep(3)
