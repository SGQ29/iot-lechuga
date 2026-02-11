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

# ===== ENDPOINT PARA RECIBIR DATOS DEL ESP32 =====
@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales

    try:
        payload = request.json

        datos_actuales = {
            "temperatura": round(payload.get("temperatura", 0), 1),
            "humedad_aire": round(payload.get("humedad_aire", 0), 1),
            "humedad_suelo": payload.get("humedad_suelo", 0),
            "luminosidad": payload.get("luminosidad", 0),
            "lux_p": round(payload.get("lux_p", 0), 1),
            "estado": payload.get("estado", "OK")
        }

        print("📥 Datos recibidos vía HTTP:", datos_actuales)

        return {"status": "ok"}, 200

    except Exception as e:
        print("❌ Error procesando datos:", e)
        return {"status": "error"}, 400


# ===== RUTAS WEB =====
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/datos")
def datos():
    return jsonify(datos_actuales)


# ===== INICIO =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

