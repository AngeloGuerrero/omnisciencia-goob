import os, time, requests, json, io, contextlib
from datetime import datetime

# --- CONFIGURACIÓN v6.3 (VINCULACIÓN TOTAL) ---
# Chocho ahora sabe que su ADN viene de GitHub y vive en G:
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"
DISCOS = ['C', 'G', 'H', 'I', 'J']

def enviar_latido():
    """Reporta latido dual para que la Web v8.0 lo vea en verde."""
    estados = {l: ("OK" if os.path.exists(f"{l}:/") else "OFFLINE") for l in DISCOS}
    ahora = time.time()
    payload = {
        "last_seen": ahora, 
        "last_heartbeat": ahora, 
        "discos": estados, 
        "ts_human": datetime.now().strftime("%H:%M:%S"), 
        "v": "6.3-SYNC",
        "status": "OPERATIVO"
    }
    try:
        requests.put(f"{FIREBASE_URL}/status/chocho.json", json=payload, timeout=5)
        requests.patch(f"{FIREBASE_URL}/status/skynet.json", json={"last_heartbeat": ahora}, timeout=5)
        print(f"💓 LATIDO SINCRONIZADO: {datetime.now().strftime('%H:%M:%S')} | Imperio OK")
    except: pass

if __name__ == "__main__":
    print("🚀 AGENTE CHOCHO v6.3 | NODO G: | ADN SINCRONIZADO CON GITHUB")
    while True:
        enviar_latido()
        try:
            res = requests.get(f"{FIREBASE_URL}/ordenes.json", timeout=5)
            if res.status_code == 200 and res.json():
                ordenes = res.json()
                for key, data in ordenes.items():
                    cmd, payload = data.get("command"), data.get("payload", {})
                    
                    if cmd == "ejecutar_habilidad":
                        print(f"🛠️ Ejecutando Habilidad Remota: {key}")
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            try: exec(payload.get("codigo", ""))
                            except Exception as e: print(f"❌ Error: {e}")
                        requests.post(f"{FIREBASE_URL}/respuestas.json", json={
                            "command_id": key, "content": output.getvalue(), "ts": time.time()
                        })

                    elif cmd == "force_github_sync":
                        print("🔄 Orden de Sincronía Recibida. Reiniciando...")
                        exit() # El .bat hará el 'git pull' y lo revivirá actualizado.

                    requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
        except: time.sleep(2)
        time.sleep(3)
