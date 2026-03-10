import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN v5.3 (SELLO DE ORO - CENTRALIZACIÓN TOTAL) ---
# G: TRABAJO (G:/Mi unidad/2-GUBA/omniscienc_ia/Programación)
# J: BÓVEDA (J:/Mi unidad/OmnisciencIA_Chocho_Data)
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

# Rutas Maestras según Capturas del Director
RUTA_G = r"G:/Mi unidad/2-GUBA/omniscienc_ia/Programación"
RUTA_J_BUNKER = r"J:/Mi unidad/OmnisciencIA_Chocho_Data"
RUTA_LOGS = os.path.join(RUTA_J_BUNKER, "logs")
ARCHIVO_CEREBRO = os.path.join(RUTA_J_BUNKER, "Cerebro_Metadatos.json")

def reportar(msg):
    """Reporte de ejecución para la interfaz web"""
    try:
        requests.post(f"{FIREBASE_URL}/respuestas.json", json={
            "content": str(msg), 
            "ts": time.time(),
            "v": "5.3"
        }, timeout=5)
    except: pass

def guardar_log_maestro(texto):
    """Escribe la auditoría permanente en el búnker J:"""
    try:
        if not os.path.exists(RUTA_LOGS): os.makedirs(RUTA_LOGS)
        fecha = datetime.now().strftime("%Y-%m-%d")
        archivo = os.path.join(RUTA_LOGS, f"auditoria_{fecha}.txt")
        with open(archivo, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {texto}\n")
    except Exception as e: print(f"Error Log J: {e}")

def enviar_latido():
    """Pulso de sincronía dual G/J"""
    try:
        g_status = "OK" if os.path.exists(RUTA_G) else "OFFLINE"
        j_status = "OK" if os.path.exists(RUTA_LOGS) else "OFFLINE"
        
        payload = {
            "last_seen": time.time(),
            "drive_g": g_status,
            "drive_j": j_status,
            "ts_human": datetime.now().strftime("%H:%M:%S"),
            "status": "ONLINE",
            "v": "5.3"
        }
        # PUT para sobreescribir y evitar datos residuales
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json=payload, timeout=5)
        print(f"💓 G:{g_status} | J:{j_status} | {payload['ts_human']} (v5.3)")
    except: pass

if __name__ == "__main__":
    print("====================================================")
    print("🚀 AGENTE CHOCHO v5.3 | MODO SELLO DE ORO")
    print("   G: OPERACIÓN | J: BÓVEDA CENTRAL")
    print("====================================================")
    
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
                        
                        resultado = output.getvalue()
                        guardar_log_maestro(f"EJECUCIÓN: {codigo[:120]}...")
                        reportar(resultado or "✅ Orden cumplida sin errores.")

                    elif cmd == "save_stable_version":
                        codigo = payload.get("codigo")
                        # Guardamos copia de seguridad en disco de trabajo G:
                        with open(os.path.join(RUTA_G, "interfaz_ESTABLE.py"), "w", encoding="utf-8") as f:
                            f.write(codigo)
                        guardar_log_maestro("SELLO DE ADN ESTABLE ACTUALIZADO EN G:")
                        reportar("✅ Sello de Identidad guardado en G:.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except: pass
        time.sleep(3)
