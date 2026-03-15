import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN v6.1 (NÚCLEO OMNIPOTENTE) ---
FIREBASE_URL = "[https://omnisciencia-cb0c0-default-rtdb.firebaseio.com](https://omnisciencia-cb0c0-default-rtdb.firebaseio.com)"
DISCOS = ['C', 'G', 'H', 'I', 'J']
# Buscamos las llaves en la misma carpeta
RUTA_JSON_KEYS = os.path.join(os.path.dirname(__file__), "gptgeminiclaude.json")

def enviar_latido():
    estados = {l: ("OK" if os.path.exists(f"{l}:/") else "OFFLINE") for l in DISCOS}
    ahora = time.time()
    
    payload = {
        "last_seen": ahora, 
        "last_heartbeat": ahora, 
        "discos": estados, 
        "ts_human": datetime.now().strftime("%H:%M:%S"), 
        "v": "6.1",
        "status": "OPERATIVO"
    }
    
    try:
        # Sincronía Dual: Chocho informa y Skynet se mantiene viva
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json=payload, timeout=5)
        requests.patch(f"{FIREBASE_URL}/status/skynet.json", json={"last_heartbeat": ahora}, timeout=5)
        print(f"💓 LATIDO NÚCLEO G: {datetime.now().strftime('%H:%M:%S')} | Discos: {estados}")
    except Exception as e:
        print(f"⚠️ Error de enlace: {e}")

if __name__ == "__main__":
    print("====================================================")
    print("   🚀 NÚCLEO CHOCHO v6.1 - MODO OMNIPOTENTE G:     ")
    print("====================================================")
    
    while True:
        enviar_latido()
        try:
            res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=5)
            if res.status_code == 200 and res.json():
                ordenes = res.json()
                for key, data in ordenes.items():
                    cmd, payload = data.get("command"), data.get("payload", {})
                    if cmd == "ejecutar_habilidad":
                        print(f"🛠️ Ejecutando habilidad: {key}")
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            try: exec(payload.get("codigo", ""))
                            except Exception as e: print(f"❌ Error: {e}")
                        requests.post(f"{FIREBASE_URL}/respuestas.json", json={
                            "command_id": key,
                            "content": output.getvalue(), 
                            "ts": time.time()
                        })
                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except: time.sleep(2)
        time.sleep(3)
