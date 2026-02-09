import paho.mqtt.client as mqtt
import requests
import json

BROKER = "broker.hivemq.com"
TOPIC = "tesis/sergio/lechuga/global"
RENDER_URL = "https://iot-lechuga.onrender.com/api/mqtt"

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print("📥 MQTT:", data)
    r = requests.post(RENDER_URL, json=data)
    print("➡️ HTTP:", r.status_code)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print("🟢 Puente MQTT → Render activo")
client.loop_forever()
