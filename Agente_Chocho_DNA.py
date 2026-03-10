import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN LOCAL ---
RUTA_PROGRAMACION = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def reportar(msg):
    try:
        requests.post(f"{FIREBASE_URL}/respuestas.json", json={"content": str(msg), "ts": time.time()})
    except: pass

def latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json={"last_seen": time.time()})
    except: pass

if __name__ == "__main__":
    print("🚀 CHOCHO v3.9 DNA - INICIADO")
    while True:
        latido()
        try:
            res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=5)
            if res.status_code == 200 and res.json():
                ordenes = res.json()
                for key, data in ordenes.items():
                    cmd = data.get("command")
                    payload = data.get("payload", {})
                    
                    if cmd == "save_stable_version":
                        path = os.path.join(RUTA_PROGRAMACION, "interfaz_ESTABLE.py")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(payload.get("codigo", ""))
                        reportar(f"✅ SELLO CREADO: {datetime.now().strftime('%H:%M:%S')}")

                    elif cmd == "ejecutar_habilidad":
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            try:
                                exec(payload.get("codigo", ""))
                            except Exception as e:
                                print(f"❌ ERROR: {e}")
                        reportar(output.getvalue() or "✅ Ejecutado sin salida.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except: pass
        time.sleep(3)

