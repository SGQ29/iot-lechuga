from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__, template_folder="templates", static_folder="static")

# ===== DATOS GLOBALES =====
datos_actuales = {
    "temperatura": 0,
    "humedad_aire": 0,
    "humedad_suelo": 0,
    "luminosidad": 0,
    "lux_p": 0,
    "estado": "SIN DATOS"
}

# ===== RUTAS =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/datos")
def datos():
    return jsonify(datos_actuales)

@app.route("/api/mqtt", methods=["POST"])
def recibir_mqtt():
    global datos_actuales
    data = request.json
    if data:
        datos_actuales.update({
            "temperatura": data.get("temperatura", 0),
            "humedad_aire": data.get("humedad_aire", 0),
            "humedad_suelo": data.get("humedad_suelo", 0),
            "luminosidad": data.get("luminosidad", 0),
            "lux_p": data.get("luminosidad", 0),
            "estado": data.get("estado", "OK")
        })
    return {"status": "ok"}


