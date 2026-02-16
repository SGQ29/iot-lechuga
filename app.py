from flask import Flask, render_template, jsonify, request, Response
import time
import sqlite3
import requests
import os
import io
import csv
from datetime import datetime

app = Flask(__name__)

# CONFIGURACIÓN
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")

sistema_encendido = True
ultimo_estado = "SIN DATOS"
datos_actuales = {
    "temperatura": 0, "humedad_aire": 0, "humedad_suelo": 0,
    "luminosidad": 0, "lux_p": 0, "estado": "SIN DATOS", "ultima_actualizacion": 0
}

DB_PATH = "datos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Aseguramos 6 columnas: timestamp, temp, h_aire, h_suelo, luz, estado
    c.execute('''CREATE TABLE IF NOT EXISTS monitoreo
                 (timestamp REAL, temperatura REAL, humedad_aire REAL, 
                  humedad_suelo REAL, luminosidad REAL, estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado
    if not sistema_encendido:
        return {"status": "sistema_apagado"}, 200

    payload = request.get_json(force=True)
    temp = round(payload.get("temperatura", 0), 1)
    h_aire = round(payload.get("humedad_aire", 0), 1)
    h_suelo = payload.get("humedad_suelo", 0)
    luz = payload.get("luminosidad", 0)
    lux_p = payload.get("lux_p", 0) # Porcentaje opcional

    # Lógica de alertas
    alertas = []
    if not (18 <= temp <= 24): alertas.append("TEMP")
    if not (60 <= h_aire <= 80): alertas.append("H.AIRE")
    if not (65 <= h_suelo <= 80): alertas.append("H.SUELO")
    if not (60 <= luz <= 85): alertas.append("LUZ")

    estado = "ÓPTIMO" if not alertas else "ALERTA: " + ", ".join(alertas)
    ts = time.time()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)", (ts, temp, h_aire, h_suelo, luz, estado))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error DB: {e}")

    datos_actuales.update({
        "temperatura": temp, "humedad_aire": h_aire, "humedad_suelo": h_suelo,
        "luminosidad": luz, "lux_p": lux_p, "estado": estado, "ultima_actualizacion": ts
    })
    return {"status": "ok"}, 200

@app.route("/control", methods=["POST"])
def control():
    global sistema_encendido
    accion = request.json.get("accion")
    sistema_encendido = (accion == "encender")
    return jsonify({"status": "ok", "sistema_encendido": sistema_encendido})

@app.route("/")
def index(): return render_template("index.html")

@app.route("/datos")
def datos():
    if not sistema_encendido: return jsonify({"estado": "SISTEMA APAGADO"})
    if time.time() - datos_actuales["ultima_actualizacion"] > 30:
        return jsonify({"estado": "DESCONECTADO", "temperatura":0, "humedad_aire":0, "humedad_suelo":0, "luminosidad":0, "lux_p":0})
    return jsonify(datos_actuales)

@app.route("/historial")
def historial():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, temperatura, humedad_aire, humedad_suelo, luminosidad, estado FROM monitoreo ORDER BY timestamp DESC LIMIT 100")
    filas = c.fetchall()
    conn.close()
    return jsonify([{"fecha": datetime.fromtimestamp(f[0]).strftime("%Y-%m-%d %H:%M:%S"), "temperatura": f[1], "humedad_aire": f[2], "humedad_suelo": f[3], "luminosidad": f[4], "estado": f[5]} for f in filas])

@app.route("/descargar")
def descargar():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM monitoreo ORDER BY timestamp DESC")
    filas = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Temperatura', 'H.Aire', 'H.Suelo', 'Luminosidad', 'Estado'])
    for f in filas:
        fecha = datetime.fromtimestamp(f[0]).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([fecha, f[1], f[2], f[3], f[4], f[5]])

    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=historial_cultivo.csv"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
