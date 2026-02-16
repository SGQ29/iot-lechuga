let miGrafica;
let sistemaActivo = true;

// Inicialización segura de la gráfica al cargar la página
window.onload = function() {
    let canvas = document.getElementById("graficoMultivariable");
    if (canvas) {
        let ctx = canvas.getContext("2d");
        miGrafica = new Chart(ctx, {
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
            options: { animation: false, responsive: true, scales: { y: { min: 0, max: 100 } } }
        });
    }
};

// Bucle de actualización
setInterval(() => {
    if (!sistemaActivo) return;
    fetch("/datos")
        .then(res => res.json())
        .then(data => {
            if (data.estado === "SISTEMA APAGADO") { 
                apagarUI(); 
            } else {
                actualizarUI(data);
                if (miGrafica) actualizarGrafica(data);
            }
        })
        .catch(err => console.error("Error al obtener datos:", err));
}, 2000);

function actualizarUI(data) {
    document.getElementById("temperatura").innerText = data.temperatura ?? "--";
    document.getElementById("humedad_aire").innerText = data.humedad_aire ?? "--";
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo ?? "--";
    document.getElementById("luminosidad").innerText = data.luminosidad ?? "--";
    
    const luxPElement = document.getElementById("lux_p");
    if (luxPElement) luxPElement.innerText = data.lux_p || 0;

    evaluar("temp", data.temperatura, 18, 24);
    evaluar("humAir", data.humedad_aire, 60, 80);
    evaluar("humSoil", data.humedad_suelo, 65, 80);
    evaluar("lux", data.luminosidad, 60, 85);

    verificarCultivo(data);
}

function evaluar(id, val, min, max) {
    const el = document.getElementById(id);
    if (el) el.className = (val >= min && val <= max) ? "card verde" : "card rojo";
}

function verificarCultivo(data) {
    const box = document.getElementById("mensaje-adecuado");
    if (!box) return;
    if (data.estado === "ÓPTIMO") {
        box.innerText = "✅ CULTIVO EN CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = "⚠️ " + (data.estado || "ALERTA");
        box.className = "diagnostico-box estado-alerta";
    }
}

function actualizarGrafica(d) {
    if (!miGrafica) return;
    if (miGrafica.data.labels.length > 20) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }
    miGrafica.data.labels.push(new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.luminosidad);
    miGrafica.update("none");
}

function controlSistema(estado) {
    fetch("/control", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({accion: estado === "on" ? "encender" : "apagar"})
    }).then(res => res.json()).then(data => {
        const stTxt = document.getElementById("estado-sistema");
        if (estado === "on") {
            sistemaActivo = true;
            stTxt.innerText = "🟢 SISTEMA ACTIVO";
            stTxt.style.color = "#27ae60";
        } else {
            sistemaActivo = false;
            apagarUI();
        }
    }).catch(err => console.error("Error en control:", err));
}

function apagarUI() {
    document.querySelectorAll("span").forEach(s => s.innerText = "--");
    document.getElementById("mensaje-adecuado").innerText = "🔴 SISTEMA APAGADO";
    document.getElementById("mensaje-adecuado").className = "diagnostico-box estado-alerta";
    document.getElementById("estado-sistema").innerText = "🔴 SISTEMA APAGADO";
    document.getElementById("estado-sistema").style.color = "#c0392b";
    if (miGrafica) {
        miGrafica.data.labels = [];
        miGrafica.data.datasets.forEach(ds => ds.data = []);
        miGrafica.update();
    }
}

function cargarHistorial() {
    fetch("/historial").then(res => res.json()).then(data => {
        const tbody = document.querySelector("#tabla-historial tbody");
        tbody.innerHTML = "";
        data.forEach(r => {
            const fila = document.createElement("tr");
            fila.innerHTML = `<td>${r.fecha}</td><td>${r.temperatura}</td><td>${r.humedad_aire}</td><td>${r.humedad_suelo}</td><td>${r.luminosidad}</td><td>${r.estado}</td>`;
            tbody.appendChild(fila);
        });
    });
}

function descargarHistorial() { 
    window.location.href = "/descargar"; 
}


