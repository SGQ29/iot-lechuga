from flask import Flask, render_template, jsonify, request
import time
import sqlite3
import requests
import os
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")

# ==============================
# CONFIGURACIÓN PUSHOVER
# ==============================

PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")

evento_critico_activo = False

def enviar_notificacion(titulo, mensaje):
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        return

    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "title": titulo,
                "message": mensaje,
                "priority": 1
            },
            timeout=5
        )
    except Exception as e:
        print("Error enviando notificación:", e)

# ==============================
# VARIABLES GLOBALES
# ==============================

sistema_encendido = True
ultimo_estado = "SIN DATOS"

datos_actuales = {
    "temperatura": 0,
    "humedad_aire": 0,
    "humedad_suelo": 0,
    "luminosidad": 0,
    "estado": "SIN DATOS",
    "ultima_actualizacion": 0
}

# ==============================
# RANGOS ÓPTIMOS
# ==============================

TEMP_MIN = 18
TEMP_MAX = 24
HUM_AIRE_MIN = 60
HUM_AIRE_MAX = 80
HUM_SUELO_MIN = 65
HUM_SUELO_MAX = 80
LUZ_MIN = 60
LUZ_MAX = 85

# ==============================
# BASE DE DATOS
# ==============================

DB_PATH = "datos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS monitoreo
                 (timestamp REAL,
                  temperatura REAL,
                  humedad_aire REAL,
                  humedad_suelo REAL,
                  luminosidad REAL,
                  estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

def generar_resumen_diario():
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT temperatura, humedad_aire, humedad_suelo, luminosidad, estado FROM monitoreo WHERE timestamp >= ?", (hoy_inicio,))
    registros = c.fetchall()
    conn.close()

    if not registros:
        return "No hay registros hoy."

    temps = [r[0] for r in registros]
    hum_aire = [r[1] for r in registros]
    hum_suelo = [r[2] for r in registros]
    luz = [r[3] for r in registros]
    alertas = [r[4] for r in registros if "ALERTA" in r[4]]

    resumen = f"""
📊 RESUMEN DEL DÍA

Registros totales: {len(registros)}
Alertas totales: {len(alertas)}

Temperatura Promedio: {round(sum(temps)/len(temps),1)}°C
Máxima: {max(temps)}°C
Mínima: {min(temps)}°C

Humedad Aire Promedio: {round(sum(hum_aire)/len(hum_aire),1)}%
Humedad Suelo Promedio: {round(sum(hum_suelo)/len(hum_suelo),1)}%
Luminosidad Promedio: {round(sum(luz)/len(luz),1)}%
"""
    return resumen

# ==============================
# RECIBIR DATOS ESP32
# ==============================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado, evento_critico_activo

    if not sistema_encendido:
        return {"status": "apagado"}, 403

    payload = request.json

    temp = round(payload.get("temperatura", 0), 1)
    hum_aire = round(payload.get("humedad_aire", 0), 1)
    hum_suelo = payload.get("humedad_suelo", 0)
    luz = payload.get("luminosidad", 0)

    alertas = []

    if not (TEMP_MIN <= temp <= TEMP_MAX):
        alertas.append("TEMPERATURA")
    if not (HUM_AIRE_MIN <= hum_aire <= HUM_AIRE_MAX):
        alertas.append("HUMEDAD AIRE")
    if not (HUM_SUELO_MIN <= hum_suelo <= HUM_SUELO_MAX):
        alertas.append("HUMEDAD SUELO")
    if not (LUZ_MIN <= luz <= LUZ_MAX):
        alertas.append("LUMINOSIDAD")

    estado = "ÓPTIMO" if not alertas else "ALERTA: " + ", ".join(alertas)

    timestamp = time.time()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)",
                  (timestamp, temp, hum_aire, hum_suelo, luz, estado))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error DB:", e)

    # Notificación cambio de estado
    if estado != ultimo_estado and estado != "ÓPTIMO":
        mensaje = (
            f"{estado}\n\n"
            f"🌡 Temp: {temp}°C\n"
            f"💧 H.Aire: {hum_aire}%\n"
            f"🌱 H.Suelo: {hum_suelo}%\n"
            f"☀ Luz: {luz}%"
        )
        enviar_notificacion("⚠ ALERTA CULTIVO LECHUGA", mensaje)

    ultimo_estado = estado

    # Detección crítica (solo Pushover)
    critico = False
    if temp > 30 or temp < 15:
        critico = True
    if hum_aire > 90 or hum_aire < 40:
        critico = True
    if hum_suelo < 50:
        critico = True
    if luz < 30:
        critico = True

    if critico and not evento_critico_activo:
        resumen = generar_resumen_diario()
        enviar_notificacion("🚨 ALERTA CRÍTICA", resumen)
        evento_critico_activo = True

    if not critico:
        evento_critico_activo = False

    datos_actuales = {
        "temperatura": temp,
        "humedad_aire": hum_aire,
        "humedad_suelo": hum_suelo,
        "luminosidad": luz,
        "estado": estado,
        "ultima_actualizacion": timestamp
    }

    return {"status": "ok"}, 200

@app.route("/estado")
def estado():
    return jsonify({"estado": sistema_encendido})

@app.route("/control", methods=["POST"])
def control():
    global sistema_encendido
    data = request.json

    if data["accion"] == "apagar":
        sistema_encendido = False
    elif data["accion"] == "encender":
        sistema_encendido = True

    return {"estado": sistema_encendido}

@app.route("/datos")
def datos():

    if not sistema_encendido:
        return jsonify({"estado": "SISTEMA APAGADO"})

    tiempo_sin_datos = time.time() - datos_actuales["ultima_actualizacion"]

    if tiempo_sin_datos > 40:
        return jsonify({
            "estado": "DESCONECTADO",
            "temperatura": 0,
            "humedad_aire": 0,
            "humedad_suelo": 0,
            "luminosidad": 0
        })

    return jsonify(datos_actuales)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
