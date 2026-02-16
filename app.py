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
ultimo_estado = "SIN DATOS"

# Estructura de datos completa para evitar errores en el JS
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
    # Aseguramos la estructura de la tabla
    c.execute('''CREATE TABLE IF NOT EXISTS monitoreo
                 (timestamp REAL, temperatura REAL, humedad_aire REAL, 
                  humedad_suelo REAL, luminosidad REAL, estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==============================
# RUTAS DE API (DATOS Y CONTROL)
# ==============================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    global datos_actuales, ultimo_estado
    
    if not sistema_encendido:
        return jsonify({"status": "sistema_apagado"}), 200

    try:
        payload = request.get_json(force=True)
        
        # Extracción de datos con valores por defecto
        temp = round(payload.get("temperatura", 0), 1)
        h_aire = round(payload.get("humedad_aire", 0), 1)
        h_suelo = payload.get("humedad_suelo", 0)
        luz = payload.get("luminosidad", 0)
        lux_p = payload.get("lux_p", 0) 

        # Lógica de estados/alertas
        alertas = []
        if not (18 <= temp <= 24): alertas.append("TEMP")
        if not (60 <= h_aire <= 80): alertas.append("H.AIRE")
        if not (65 <= h_suelo <= 80): alertas.append("H.SUELO")
        if not (60 <= luz <= 85): alertas.append("LUZ")

        estado = "ÓPTIMO" if not alertas else "ALERTA: " + ", ".join(alertas)
        ts = time.time()

        # Guardado en Base de Datos
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO monitoreo VALUES (?,?,?,?,?,?)", 
                  (ts, temp, h_aire, h_suelo, luz, estado))
        conn.commit()
        conn.close()

        # Actualización de variables globales
        datos_actuales.update({
            "temperatura": temp, 
            "humedad_aire": h_aire, 
            "humedad_suelo": h_suelo,
            "luminosidad": luz, 
            "lux_p": lux_p, 
            "estado": estado, 
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
        # Forzamos el cambio de la variable global
        if accion == "encender":
            sistema_encendido = True
        else:
            sistema_encendido = False
            
        return jsonify({"status": "ok", "sistema_encendido": sistema_encendido})
    except Exception as e:
        print(f"Error en control: {e}")
        return jsonify({"status": "error"}), 400
# ==============================
# RUTAS PARA EL FRONTEND (WEB)
# ==============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/estado")
def estado():
    """Ruta para resolver los errores 404 en los logs de Render"""
    return jsonify({
        "sistema_activo": sistema_encendido,
        "estado": "SISTEMA ACTIVO" if sistema_encendido else "SISTEMA APAGADO"
    })

@app.route("/datos")
def datos():
    if not sistema_encendido:
        return jsonify({"estado": "SISTEMA APAGADO"})
    
    # Verificación de desconexión (si no hay datos nuevos en 40 segundos)
    if time.time() - datos_actuales["ultima_actualizacion"] > 40:
        return jsonify({
            "estado": "DESCONECTADO",
            "temperatura": 0, "humedad_aire": 0, "humedad_suelo": 0, "luminosidad": 0, "lux_p": 0
        })
    
    return jsonify(datos_actuales)

# ==============================
# HISTORIAL Y DESCARGA CSV
# ==============================

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

    # Generación de CSV en memoria
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

