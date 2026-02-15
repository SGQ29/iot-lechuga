from flask import Flask, render_template, jsonify, request
import time
import sqlite3
import requests
import os

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
            timeout=3
        )
    except:
        pass


# ==============================
# VARIABLES GLOBALES
# ==============================

sistema_encendido = True
ultimo_estado = "SIN DATOS"

ALPHA = 0.4

datos_actuales = {
    "temperatura": 0.0,
    "humedad_aire": 0.0,
    "humedad_suelo": 0.0,
    "luminosidad": 0.0,
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
# FILTRO EMA
# ==============================

def ema(nuevo, anterior):
    return (ALPHA * nuevo) + ((1 - ALPHA) * anterior)

# ==============================
# API RECEPCIÓN ESP32
# ==============================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado, evento_critico_activo

    if not sistema_encendido:
        return {"status": "apagado"}, 403

    payload = request.get_json(force=True)
    timestamp = time.time()

    temp = round(ema(payload.get("temperatura", 0), datos_actuales["temperatura"]), 1)
    hum_aire = round(ema(payload.get("humedad_aire", 0), datos_actuales["humedad_aire"]), 1)
    hum_suelo = round(ema(payload.get("humedad_suelo", 0), datos_actuales["humedad_suelo"]), 1)
    luz = round(ema(payload.get("luminosidad", 0), datos_actuales["luminosidad"]), 1)

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

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)",
                  (timestamp, temp, hum_aire, hum_suelo, luz, estado))
        conn.commit()
        conn.close()
    except:
        pass

    if estado != ultimo_estado and estado != "ÓPTIMO":
        enviar_notificacion("⚠ ALERTA CULTIVO", estado)

    ultimo_estado = estado

    datos_actuales.update({
        "temperatura": temp,
        "humedad_aire": hum_aire,
        "humedad_suelo": hum_suelo,
        "luminosidad": luz,
        "estado": estado,
        "ultima_actualizacion": timestamp
    })

    return {"status": "ok"}, 200


# ==============================
# ENDPOINTS WEB
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/estado")
def estado():
    return jsonify({"estado": sistema_encendido})


@app.route("/datos")
def datos():
    if time.time() - datos_actuales["ultima_actualizacion"] > 15:
        return jsonify({"estado": "DESCONECTADO"})
    return jsonify(datos_actuales)


# IMPORTANTE PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
