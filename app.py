import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify
import json
import threading

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

# ===== MQTT =====
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "tesis/sergio/lechuga/global"

def on_message(client, userdata, message):
    global datos_actuales
    print("📥 Mensaje recibido:", message.payload.decode())
    try:
        payload = json.loads(message.payload.decode())
        datos_actuales.update({
            "temperatura": round(payload.get("temperatura", 0), 1),
            "humedad_aire": round(payload.get("humedad_aire", 0), 1),
            "humedad_suelo": payload.get("humedad_suelo", 0),
            "luminosidad": payload.get("luminosidad", 0),
            "lux_p": round(payload.get("luminosidad", 0), 1),
            "estado": payload.get("estado", "OK")
        })
    except Exception as e:
        print("❌ Error MQTT:", e)

def mqtt_loop():
    client = mqtt.Client()
    client.on_message = on_message

    while True:
        try:
            print("🔌 Conectando a MQTT...")
            client.connect(MQTT_BROKER, 1883, 60)
            client.subscribe(MQTT_TOPIC)
            print("📡 Suscrito a:", MQTT_TOPIC)
            client.loop_forever()
        except Exception as e:
            print("❌ Error MQTT:", e)


# HILO MQTT
threading.Thread(target=mqtt_loop, daemon=True).start()

# ===== FLASK =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/datos")
def datos():
    return jsonify(datos_actuales)

