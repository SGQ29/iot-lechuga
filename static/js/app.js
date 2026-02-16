// --- CONFIGURACIÓN INICIAL DEL GRÁFICO ---
let ctx = document.getElementById("graficoMultivariable").getContext("2d");
let sistemaActivo = true;

let miGrafica = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "Temp", data: [], borderColor: "#e74c3c", tension: 0.3 },
            { label: "H.Aire", data: [], borderColor: "#3498db", tension: 0.3 },
            { label: "H.Suelo", data: [], borderColor: "#e67e22", tension: 0.3 },
            { label: "Luz", data: [], borderColor: "#f1c40f", tension: 0.3 }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        scales: {
            y: { min: 0, max: 100 }
        }
    }
});

// --- BUCLE DE MONITOREO EN TIEMPO REAL ---
setInterval(() => {
    if (!sistemaActivo) return;

    fetch("/datos")
    .then(res => res.json())
    .then(data => {
        if (data.estado === "SISTEMA APAGADO") {
            apagarUI();
            return;
        }

        if (data.estado === "DESCONECTADO") {
            document.getElementById("mensaje-adecuado").innerText = "⚠️ DISPOSITIVO DESCONECTADO";
            return;
        }

        actualizarUI(data);
        actualizarGrafica(data);
    })
    .catch(err => console.error("Error obteniendo datos:", err));
}, 800); 

// --- FUNCIONES DE INTERFAZ (UI) ---
function actualizarUI(data) {
    document.getElementById("temperatura").innerText = data.temperatura ?? 0;
    document.getElementById("humedad_aire").innerText = data.humedad_aire ?? 0;
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo ?? 0;
    document.getElementById("luminosidad").innerText = data.luminosidad ?? 0;
    document.getElementById("lux_p").innerText = data.lux_p ?? 0;

    evaluar("temp", data.temperatura, 18, 24);
    evaluar("humAir", data.humedad_aire, 60, 80);
    evaluar("humSoil", data.humedad_suelo, 65, 80);
    evaluar("lux", data.luminosidad, 60, 85);

    verificarCultivo(data);
}

function evaluar(id, val, min, max) {
    const el = document.getElementById(id);
    if (val >= min && val <= max) {
        el.className = "card verde";
    } else {
        el.className = "card rojo";
    }
}

function verificarCultivo(data) {
    const box = document.getElementById("mensaje-adecuado");
    if (data.estado === "ÓPTIMO") {
        box.innerText = "✅ CULTIVO EN CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = "⚠️ " + data.estado;
        box.className = "diagnostico-box estado-alerta";
    }
}

function actualizarGrafica(d) {
    if (miGrafica.data.labels.length > 20) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }

    miGrafica.data.labels.push("");
    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.luminosidad);

    miGrafica.update("none");
}

// --- CONTROLES DEL SISTEMA ---
function controlSistema(estado) {
    fetch("/control", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({accion: estado === "on" ? "encender" : "apagar"})
    });

    const stTxt = document.getElementById("estado-sistema");
    if (estado === "on") {
        sistemaActivo = true;
        stTxt.innerText = "🟢 SISTEMA ACTIVO";
        stTxt.style.color = "#27ae60";
    } else {
        sistemaActivo = false;
        apagarUI();
    }
}

function apagarUI() {
    document.querySelectorAll("span").forEach(s => s.innerText = "--");
    document.getElementById("mensaje-adecuado").innerText = "🔴 SISTEMA APAGADO";
    document.getElementById("mensaje-adecuado").className = "diagnostico-box estado-alerta";
    document.getElementById("estado-sistema").innerText = "🔴 SISTEMA APAGADO";
    document.getElementById("estado-sistema").style.color = "#c0392b";

    miGrafica.data.labels = [];
    miGrafica.data.datasets.forEach(ds => ds.data = []);
    miGrafica.update("none");
}

// --- GESTIÓN DEL HISTORIAL ---
function cargarHistorial() {
    fetch("/historial")
    .then(res => res.json())
    .then(data => {
        const tbody = document.querySelector("#tabla-historial tbody");
        tbody.innerHTML = "";
        data.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${r.fecha}</td>
                <td>${r.temperatura} °C</td>
                <td>${r.humedad_aire} %</td>
                <td>${r.humedad_suelo} %</td>
                <td>${r.luminosidad}</td>
                <td>${r.estado}</td>
            `;
            tbody.appendChild(tr);
        });
    })
    .catch(err => console.error("Error cargando historial:", err));
}

function descargarHistorial() {
    window.location.href = "/descargar";
}

