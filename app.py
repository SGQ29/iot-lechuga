from flask import Flask, render_template, jsonify, request, Response
import time
import sqlite3
import requests
import os
import io
import csv
from datetime import datetime

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN Y VARIABLES
# ==============================
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")

sistema_encendido = True
ultimo_estado_alerta = "ÓPTIMO" # Para evitar spam de notificaciones

datos_actuales = {
    "temperatura": 0, 
    "humedad_aire": 0, 
    "humedad_suelo": 0,
    "luminosidad": 0, 
    "lux_p": 0, 
    "estado": "SIN DATOS", 
    "ultima_actualizacion": 0
}

DB_PATH = "datos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS monitoreo
                 (timestamp REAL, temperatura REAL, humedad_aire REAL, 
                  humedad_suelo REAL, luminosidad REAL, estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==============================
# FUNCIÓN PUSHOVER
# ==============================
def enviar_pushover(mensaje):
    """Envía la alerta a tu celular vía Pushover"""
    if PUSHOVER_USER and PUSHOVER_TOKEN:
        try:
            requests.post("https://api.pushover.net/1/messages.json", data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "message": mensaje,
                "title": "Alerta Cultivo Lechuga 🥬"
            }, timeout=5)
            print("Notificación enviada con éxito.")
        except Exception as e:
            print(f"Error enviando a Pushover: {e}")

# ==============================
# RUTAS DE API (DATOS Y CONTROL)
# ==============================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado_alerta
    
    if not sistema_encendido:
        return jsonify({"status": "sistema_apagado"}), 200

    try:
        payload = request.get_json(force=True)
        
        temp = round(payload.get("temperatura", 0), 1)
        h_aire = round(payload.get("humedad_aire", 0), 1)
        h_suelo = payload.get("humedad_suelo", 0)
        luz = payload.get("luminosidad", 0)
        lux_p = payload.get("lux_p", 0) 

        # Lógica de estados/alertas
        alertas = []
        if not (18 <= temp <= 24): alertas.append(f"TEMP ({temp}°C)")
        if not (60 <= h_aire <= 80): alertas.append(f"H.AIRE ({h_aire}%)")
        if not (65 <= h_suelo <= 80): alertas.append(f"H.SUELO ({h_suelo}%)")
        if not (60 <= luz <= 85): alertas.append(f"LUZ ({luz}%)")

        estado_actual = "ÓPTIMO" if not alertas else "ALERTA"
        resumen_estado = "ÓPTIMO" if not alertas else "ALERTA: " + ", ".join(alertas)
        ts = time.time()

        # --- LÓGICA DE NOTIFICACIÓN ---
        # Solo envía si el estado cambia de ÓPTIMO a ALERTA
        if estado_actual == "ALERTA" and ultimo_estado_alerta == "ÓPTIMO":
            mensaje_notif = f"Anomalía detectada:\n" + "\n".join(alertas)
            enviar_pushover(mensaje_notif)
        
        ultimo_estado_alerta = estado_actual
        # ------------------------------

        # Guardado en Base de Datos
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)", 
                  (ts, temp, h_aire, h_suelo, luz, resumen_estado))
        conn.commit()
        conn.close()

        datos_actuales.update({
            "temperatura": temp, 
            "humedad_aire": h_aire, 
            "humedad_suelo": h_suelo,
            "luminosidad": luz, 
            "lux_p": lux_p, 
            "estado": resumen_estado, 
            "ultima_actualizacion": ts
        })
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/control", methods=["POST"])
def control():
    global sistema_encendido
    try:
        data = request.get_json()
        accion = data.get("accion")
        if accion == "encender":
            sistema_encendido = True
        else:
            sistema_encendido = False
            
        return jsonify({"status": "ok", "sistema_encendido": sistema_encendido})
    except Exception as e:
        print(f"Error en control: {e}")
        return jsonify({"status": "error"}), 400

# [Resto de tus rutas: /, /estado, /datos, /historial, /descargar se mantienen igual...]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/estado")
def estado():
    return jsonify({
        "sistema_activo": sistema_encendido,
        "estado": "SISTEMA ACTIVO" if sistema_encendido else "SISTEMA APAGADO"
    })

@app.route("/datos")
def datos():
    if not sistema_encendido:
        return jsonify({"estado": "SISTEMA APAGADO"})
    if time.time() - datos_actuales["ultima_actualizacion"] > 40:
        return jsonify({
            "estado": "DESCONECTADO",
            "temperatura": 0, "humedad_aire": 0, "humedad_suelo": 0, "luminosidad": 0, "lux_p": 0
        })
    return jsonify(datos_actuales)

@app.route("/historial")
def historial():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, temperatura, humedad_aire, humedad_suelo, luminosidad, estado FROM monitoreo ORDER BY timestamp DESC LIMIT 100")
    filas = c.fetchall()
    conn.close()
    
    registros = []
    for f in filas:
        registros.append({
            "fecha": datetime.fromtimestamp(f[0]).strftime("%Y-%m-%d %H:%M:%S"),
            "temperatura": f[1],
            "humedad_aire": f[2],
            "humedad_suelo": f[3],
            "luminosidad": f[4],
            "estado": f[5]
        })
    return jsonify(registros)

@app.route("/descargar")
def descargar():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, temperatura, humedad_aire, humedad_suelo, luminosidad, estado FROM monitoreo ORDER BY timestamp DESC")
    filas = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Temperatura', 'H.Aire', 'H.Suelo', 'Luminosidad', 'Estado'])
    for f in filas:
        fecha = datetime.fromtimestamp(f[0]).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([fecha, f[1], f[2], f[3], f[4], f[5]])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=historial_lechuga_crespa.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
