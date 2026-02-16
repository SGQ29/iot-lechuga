from flask import Flask, render_template, jsonify, request
import time
import sqlite3
import requests
import os
from datetime import datetime

app = Flask(__name__)

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
    except:
        pass


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

# ==============================
# RECIBIR DATOS ESP32
# ==============================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado, evento_critico_activo

    # 🔴 SI EL SISTEMA ESTÁ APAGADO → IGNORA TODO
    if not sistema_encendido:
        return {"status": "sistema_apagado"}, 200

    payload = request.get_json(force=True)

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

    # Guardar en base
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)",
                  (timestamp, temp, hum_aire, hum_suelo, luz, estado))
        conn.commit()
        conn.close()
    except:
        pass

    # 🔔 SOLO ENVÍA ALERTAS SI ESTÁ ENCENDIDO
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

    datos_actuales = {
        "temperatura": temp,
        "humedad_aire": hum_aire,
        "humedad_suelo": hum_suelo,
        "luminosidad": luz,
        "estado": estado,
        "ultima_actualizacion": timestamp
    }

    return {"status": "ok"}, 200


# ==============================
# ENDPOINTS WEB
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/estado")
def estado():
    return jsonify({"estado": sistema_encendido})

@app.route("/datos")
def datos():

    if not sistema_encendido:
        return jsonify({"estado": "SISTEMA APAGADO"})

    if time.time() - datos_actuales["ultima_actualizacion"] > 30:
        return jsonify({
            "estado": "DESCONECTADO",
            "temperatura": 0,
            "humedad_aire": 0,
            "humedad_suelo": 0,
            "luminosidad": 0
        })

    return jsonify(datos_actuales)


# ==============================
# RENDER COMPATIBLE
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

