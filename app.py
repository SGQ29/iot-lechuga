from flask import Flask, render_template, jsonify, request
import time

app = Flask(__name__, template_folder="templates", static_folder="static")

# ===== VARIABLES GLOBALES =====
sistema_encendido = True

datos_actuales = {
    "temperatura": 0,
    "humedad_aire": 0,
    "humedad_suelo": 0,
    "luminosidad": 0,
    "estado": "SIN DATOS",
    "ultima_actualizacion": 0
}

# ===== RANGOS ÓPTIMOS LECHUGA CRESPA =====
TEMP_MIN = 18
TEMP_MAX = 24

HUM_AIRE_MIN = 60
HUM_AIRE_MAX = 80

HUM_SUELO_MIN = 65
HUM_SUELO_MAX = 80

LUZ_MIN = 60
LUZ_MAX = 85


# ===== RECIBIR DATOS DEL ESP32 =====
@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales

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

    if not (HUM_AIRE_MIN <= hum_aire <= HUM_AIRE_MAX):
        estado = "ALERTA HUMEDAD AIRE"

    if not (HUM_SUELO_MIN <= hum_suelo <= HUM_SUELO_MAX):
        estado = "ALERTA HUMEDAD SUELO"

    if not (LUZ_MIN <= luz <= LUZ_MAX):
        estado = "ALERTA LUMINOSIDAD"

    datos_actuales = {
        "temperatura": temp,
        "humedad_aire": hum_aire,
        "humedad_suelo": hum_suelo,
        "luminosidad": luz,
        "estado": estado,
        "ultima_actualizacion": time.time()
    }

    print("📥 Datos recibidos:", datos_actuales)

    return {"status": "ok"}, 200


# ===== CONTROL ENCENDER/APAGAR =====
@app.route("/control", methods=["POST"])
def control():
    global sistema_encendido
    data = request.json

    if data["accion"] == "apagar":
        sistema_encendido = False
    elif data["accion"] == "encender":
        sistema_encendido = True

    return {"estado": sistema_encendido}


# ===== ENVIAR DATOS A INTERFAZ =====
@app.route("/datos")
def datos():
    if not sistema_encendido:
        return jsonify({
            "temperatura": 0,
            "humedad_aire": 0,
            "humedad_suelo": 0,
            "luminosidad": 0,
            "estado": "SISTEMA APAGADO"
        })

    if time.time() - datos_actuales["ultima_actualizacion"] > 20:
        return jsonify({
            "temperatura": 0,
            "humedad_aire": 0,
            "humedad_suelo": 0,
            "luminosidad": 0,
            "estado": "DESCONECTADO"
        })

    return jsonify(datos_actuales)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


