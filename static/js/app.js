let charts = {};
let sistemaActivo = true;

window.onload = function() {
    const crearConfig = (label, color, unit) => ({
        type: "line",
        data: { labels: [], datasets: [{ label: `${label} (${unit})`, data: [], borderColor: color, backgroundColor: color + '22', borderWidth: 2, tension: 0.3, fill: true }] },
        options: { 
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { legend: { labels: { font: { size: 10 } } } },
            scales: { y: { beginAtZero: false, ticks: { font: { size: 10 } } }, x: { ticks: { display: false } } }
        }
    });

    charts.temp = new Chart(document.getElementById("chartTemp"), crearConfig("Temperatura", "#e74c3c", "°C"));
    charts.humAir = new Chart(document.getElementById("chartHumAir"), crearConfig("H. Aire", "#3498db", "%"));
    charts.humSoil = new Chart(document.getElementById("chartHumSoil"), crearConfig("H. Suelo", "#e67e22", "%"));
    charts.lux = new Chart(document.getElementById("chartLux"), crearConfig("Luminosidad", "#f1c40f", "%"));
};

setInterval(() => {
    if (!sistemaActivo) return;
    fetch("/datos").then(res => res.json()).then(data => {
        if (data.estado === "SISTEMA APAGADO") { apagarUI(); } 
        else { actualizarUI(data); actualizarGraficas(data); }
    });
}, 2000);

function actualizarGraficas(d) {
    const ahora = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
    const vars = [
        { id: 'temp', val: d.temperatura },
        { id: 'humAir', val: d.humedad_aire },
        { id: 'humSoil', val: d.humedad_suelo },
        { id: 'lux', val: d.luminosidad }
    ];

    vars.forEach(v => {
        let chart = charts[v.id];
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.data.labels.push(ahora);
        chart.data.datasets[0].data.push(v.val);
        chart.update("none");
    });
}

function actualizarUI(data) {
    document.getElementById("temperatura").innerText = data.temperatura ?? "--";
    document.getElementById("humedad_aire").innerText = data.humedad_aire ?? "--";
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo ?? "--";
    document.getElementById("luminosidad").innerText = data.luminosidad ?? "--";
    
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
    if (data.estado === "ÓPTIMO") {
        box.innerText = "✅ CULTIVO EN CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = "⚠️ " + (data.estado || "ALERTA");
        box.className = "diagnostico-box estado-alerta";
    }
}

function controlSistema(estado) {
    fetch("/control", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({accion: estado === "on" ? "encender" : "apagar"})
    }).then(() => {
        sistemaActivo = (estado === "on");
        if (!sistemaActivo) apagarUI();
        document.getElementById("estado-sistema").innerText = sistemaActivo ? "🟢 SISTEMA ACTIVO" : "🔴 SISTEMA APAGADO";
    });
}

function apagarUI() {
    document.querySelectorAll(".card span").forEach(s => s.innerText = "--");
    Object.values(charts).forEach(c => { c.data.labels = []; c.data.datasets[0].data = []; c.update(); });
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

function descargarHistorial() { window.location.href = "/descargar"; }
