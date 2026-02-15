from flask import Flask, render_template, jsonify, request
import time
import sqlite3
import requests
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

# ==============================
# CONFIGURACIÓN PUSHOVER
# ==============================

PUSHOVER_USER = os.environ.get("ujv1fjyjt32zgc7zn8u9uq97pn6i5j")
PUSHOVER_TOKEN = os.environ.get("ad358ypedc4ygbqvvw86h5ix1oinnc")

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
ultima_alerta = 0
TIEMPO_ALERTA = 60

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
# BASE DE DATOS (RENDER SAFE)
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
    global datos_actuales, ultima_alerta

    if not sistema_encendido:
        return {"status": "apagado"}, 403

    payload = request.json

    temp = round(payload.get("temperatura", 0), 1)
    hum_aire = round(payload.get("humedad_aire", 0), 1)
    hum_suelo = payload.get("humedad_suelo", 0)
    luz = payload.get("luminosidad", 0)

    estado = "ÓPTIMO"

    if not (TEMP_MIN <= temp <= TEMP_MAX):
        estado = "ALERTA TEMPERATURA"
    elif not (HUM_AIRE_MIN <= hum_aire <= HUM_AIRE_MAX):
        estado = "ALERTA HUMEDAD AIRE"
    elif not (HUM_SUELO_MIN <= hum_suelo <= HUM_SUELO_MAX):
        estado = "ALERTA HUMEDAD SUELO"
    elif not (LUZ_MIN <= luz <= LUZ_MAX):
        estado = "ALERTA LUMINOSIDAD"

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

    # Notificación anti-spam
    if estado != "ÓPTIMO" and (time.time() - ultima_alerta > TIEMPO_ALERTA):
        mensaje = (
            f"{estado}\n\n"
            f"Temp: {temp}°C\n"
            f"H.Aire: {hum_aire}%\n"
            f"H.Suelo: {hum_suelo}%\n"
            f"Luz: {luz}%"
        )
        enviar_notificacion("ALERTA CULTIVO LECHUGA", mensaje)
        ultima_alerta = time.time()

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

    if time.time() - datos_actuales["ultima_actualizacion"] > 15:
        return jsonify({"estado": "DESCONECTADO"})

    return jsonify(datos_actuales)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()

