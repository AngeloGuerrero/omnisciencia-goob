import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN LOCAL ---
RUTA_PROGRAMACION = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def reportar_a_nube(contenido):
    try:
        data = {"content": str(contenido), "timestamp": time.time()}
        requests.post(f"{FIREBASE_URL}/respuestas.json", json=data, timeout=5)
    except: pass

def procesar():
    try:
        # Latido de Chocho para que la web sepa que estamos vivos
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json={"last_seen": time.time()})
        
        res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=10)
        if res.status_code == 200 and res.json():
            ordenes = res.json()
            for key, data in ordenes.items():
                cmd = data.get("command")
                payload = data.get("payload", {})
                
                print(f"Executing: {cmd}")

                if cmd == "save_stable_version":
                    with open(os.path.join(RUTA_PROGRAMACION, "interfaz_ESTABLE.py"), "w", encoding="utf-8") as f:
                        f.write(payload.get("codigo", ""))
                    reportar_a_nube(f"✅ Sello creado físicamente: {datetime.now().strftime('%H:%M:%S')}")

                elif cmd == "ejecutar_habilidad":
                    # CAPTURAMOS LA SALIDA DEL CODIGO (stdout)
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        try:
                            exec(payload.get("codigo", ""))
                        except Exception as e:
                            print(f"❌ ERROR DE SINTAXIS: {e}")
                    
                    reportar_a_nube(f.getvalue() or "⚠️ Habilidad ejecutada pero no produjo texto (print).")

                requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 CHOCHO v3.8 DNA ONLINE - MODO FEEDBACK")
    while True:
        procesar()
        time.sleep(3)

