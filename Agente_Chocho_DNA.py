import os
import time
import requests
import json
from datetime import datetime

# --- CONFIGURACIÓN LOCAL DEL DISCO G: ---
# Esta ruta debe coincidir con tu carpeta de Google Drive en PC
RUTA_PROGRAMACION = r"G:\Mi unidad\2-GUBA\omniscienc_ia\Programación"
FIREBASE_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com"

def procesar_ordenes():
    try:
        # Bajamos las ordenes pendientes de Firebase
        url = f"{FIREBASE_URL}/ordenes.json"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200 and res.json():
            ordenes = res.json()
            for key, data in ordenes.items():
                # Extraemos el comando y el contenido
                comando = data.get("command")
                payload = data.get("payload", {})
                
                # --- LÓGICA DE SELLADO (LO QUE CURA LA AMNESIA) ---
                if comando == "save_stable_version":
                    codigo = payload.get("codigo")
                    ruta_estable = os.path.join(RUTA_PROGRAMACION, "interfaz_ESTABLE.py")
                    
                    # Escribimos físicamente el archivo en el disco G:
                    with open(ruta_estable, "w", encoding="utf-8") as f:
                        f.write(codigo)
                    
                    # Confirmamos a la nube con la fecha REAL de hoy
                    confirmacion = {
                        "status": "SUCCESS",
                        "content": f"✅ Respaldo físico creado el {datetime.now().strftime('%Y-%m-%d %I:%M:%S')}",
                        "timestamp": time.time()
                    }
                    requests.post(f"{FIREBASE_URL}/respuestas.json", json=confirmacion)
                    print(f"🔥 SELLO CREADO EXITOSAMENTE: {datetime.now()}")

                # --- EJECUCIÓN DE HABILIDADES DINÁMICAS ---
                elif comando == "ejecutar_habilidad":
                    code = payload.get("codigo")
                    # Esto permite que Skynet le enseñe trucos nuevos a Chocho
                    exec(code)

                # Borramos la orden para no repetirla
                requests.delete(f"{FIREBASE_URL}/ordenes/{key}.json")
                
    except Exception as e:
        print(f"⚠️ Error en ciclo Chocho: {e}")

if __name__ == "__main__":
    print("🚀 NÚCLEO CHOCHO v3.4 DNA - ACTIVADO")
    while True:
        procesar_ordenes()
        time.sleep(5) # Espera 5 segundos para no saturar la red

