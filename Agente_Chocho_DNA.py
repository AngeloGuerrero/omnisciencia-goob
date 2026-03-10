import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN LOCAL ---
RUTA_PROGRAMACION = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/AngeloGuerrero/omnisciencia-goob/main/Agente_Chocho_DNA.py"

def reportar(msg):
    try: requests.post(f"{FIREBASE_URL}/respuestas.json", json={"content": str(msg), "ts": time.time()})
    except: pass

def enviar_latido():
    try:
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json={"last_seen": time.time()})
        print(f"💓 Latido: {datetime.now().strftime('%H:%M:%S')}")
    except: print("❌ Error de red")

def mutar_desde_github():
    """Descarga el nuevo ADN y reinicia el proceso."""
    print("🚀 [MUTACIÓN] Iniciando descarga desde GitHub...")
    try:
        res = requests.get(GITHUB_RAW_URL, timeout=15)
        if res.status_code == 200:
            ruta_propia = os.path.abspath(__file__)
            with open(ruta_propia, 'w', encoding='utf-8') as f:
                f.write(res.text)
            print("✅ [OK] ADN Actualizado físicamente. Reiniciando...")
            reportar("🧬 Chocho ha mutado en tiempo real exitosamente.")
            os._exit(0) # El .bat lo revive en 5s
    except Exception as e:
        print(f"⚠️ Error en mutación: {e}")

if __name__ == "__main__":
    print("====================================================")
    print(f"🚀 AGENTE CHOCHO v4.3 (REAL-TIME) - INICIADO")
    print("====================================================")
    
    while True:
        enviar_latido()
        
        try:
            # 1. Revisar órdenes y GATILLOS de actualización
            res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=5)
            if res.status_code == 200 and res.json():
                ordenes = res.json()
                for key, data in ordenes.items():
                    cmd = data.get("command")
                    
                    # --- GATILLO DE TIEMPO REAL ---
                    if cmd == "force_github_sync":
                        print("⚡ [TRIGGER] Orden de sincronía instantánea recibida.")
                        mutar_desde_github()
                    
                    elif cmd == "ejecutar_habilidad":
                        codigo = data.get("payload", {}).get("codigo", "")
                        print("🐍 Ejecutando Habilidad...")
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            try: exec(codigo)
                            except Exception as e: print(f"❌ Error: {e}")
                        reportar(output.getvalue() or "✅ Ejecutado.")

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except Exception as e:
            print(f"⚠️ Error en ciclo: {e}")
            
        time.sleep(3) # Revisión cada 3 segundos (Casi tiempo real)
