import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN LOCAL ---
RUTA_PROGRAMACION = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def reportar(msg):
    try:
        requests.post(f"{FIREBASE_URL}/respuestas.json", json={"content": str(msg), "ts": time.time()})
    except: pass

def enviar_latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json={"last_seen": time.time()})
        # LOG VERBOSE: Confirmación visual en consola
        print(f"💓 Latido enviado a las {datetime.now().strftime('%H:%M:%S')}")
    except:
        print("❌ Error enviando latido (Revisar Internet)")

if __name__ == "__main__":
    print("====================================================")
    print(f"🚀 AGENTE CHOCHO v4.1 (VERBOSE) - INICIADO")
    print(f"📂 RUTA: {RUTA_PROGRAMACION}")
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
                    
                    print(f"🔥 ORDEN RECIBIDA: {cmd}")
                    
                    if cmd == "save_stable_version":
                        path = os.path.join(RUTA_PROGRAMACION, "interfaz_ESTABLE.py")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(payload.get("codigo", ""))
                        msg = f"✅ SELLO FÍSICO CREADO: {datetime.now().strftime('%H:%M:%S')}"
                        print(msg)
                        reportar(msg)

                    elif cmd == "ejecutar_habilidad":
                        output = io.StringIO()
                        codigo = payload.get("codigo", "")
                        print("🐍 Ejecutando Habilidad Dinámica...")
                        
                        # Reparador de imports por si Skynet falla
                        codigo = codigo.replace("import os import", "import os\nimport")
                        
                        with contextlib.redirect_stdout(output):
                            try:
                                exec(codigo)
                                print("✅ Ejecución local exitosa.")
                            except Exception as e:
                                print(f"❌ ERROR FÍSICO: {e}")
                        
                        reportar(output.getvalue() or "✅ Acción completada.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
            else:
                # Opcional: print("💤 Sin órdenes pendientes.")
                pass
        except Exception as e:
            print(f"⚠️ Error en ciclo: {e}")
            
        time.sleep(3) # Latido cada 3 segundos
