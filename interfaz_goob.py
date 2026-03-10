import os
import requests
import json
import time
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DINÁMICA DE RUTAS ---
# Detecta automáticamente la carpeta donde vive este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, 'Versiones')
LOCAL_FILE = os.path.join(BASE_DIR, 'interfaz_goob.py')
HEARTBEAT_URL = "https://omnisciencia-cb0c0-default-rtdb.firebaseio.com/status/skynet.json"

# Aseguramos que la carpeta de versiones exista para que no crashee
os.makedirs(BACKUP_DIR, exist_ok=True)

def obtener_hora():
    """Obtiene la hora de Guadalajara para los logs."""
    tz = timezone(timedelta(hours=-6))
    return datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")

def resucitar_skynet():
    """Busca el backup más reciente y sobreescribe el archivo principal."""
    versiones = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.py')]
    versiones.sort() # Orden alfabético (auto_YYYYMMDD...)
    
    if versiones:
        ultimo_backup = os.path.join(BACKUP_DIR, versiones[-1])
        print(f"[LAZARO] Resucitando desde: {versiones[-1]}")
        
        try:
            with open(ultimo_backup, 'r', encoding='utf-8') as src:
                contenido = src.read()
            with open(LOCAL_FILE, 'w', encoding='utf-8') as dest:
                dest.write(contenido)
            print(f"{obtener_hora()} - [OK] Skynet ha vuelto a la vida físicamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo escribir el archivo: {e}")
    else:
        print(f"[ERROR] No hay archivos .py en {BACKUP_DIR}. Haga un backup manual primero.")

def watchdog_loop():
    """Bucle de vigilancia eterna."""
    print("====================================================")
    print(f"   WATCHDOG SKYNET v2.1 (AUTO-PATH) - {obtener_hora()}")
    print(f"   Ruta: {BASE_DIR}")
    print("====================================================")
    
    while True:
        try:
            # Quitamos el prefijo de búsqueda de Google y vamos directo al JSON
            res = requests.get(HEARTBEAT_URL, timeout=10)
            if res.status_code == 200:
                datos = res.json()
                if datos:
                    last_beat = datos.get('last_heartbeat', 0)
                    
                    # Margen de 120 segundos para evitar paranoias
                    if time.time() - last_beat > 120:
                        print(f"\n[!] ALERTA: Heartbeat perdido ({int(time.time() - last_beat)}s). Iniciando Lázaro...")
                        resucitar_skynet()
                        time.sleep(60) # Pausa tras resucitar
                    else:
                        # Todo bien, solo imprimimos un punto para saber que sigue vivo el guardian
                        pass
                else:
                    print(f"\n[?] Firebase vacío.")
            else:
                print(f"\n[?] Firebase error: {res.status_code}")
        except Exception as e:
            print(f"\n[!] Error de red: {e}. Reintentando...")
            
        time.sleep(30) # Revisión cada 30 segundos

if __name__ == "__main__":
    watchdog_loop()
