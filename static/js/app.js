let ctx = document.getElementById("graficoMultivariable").getContext("2d");
let sistemaActivo = true;
let ultimoTimestamp = 0;

let miGrafica = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "Temp", data: [], borderColor: "#e74c3c", yAxisID: 'y' },
            { label: "H.Aire", data: [], borderColor: "#3498db", yAxisID: 'y' },
            { label: "H.Suelo", data: [], borderColor: "#e67e22", yAxisID: 'y' },
            { label: "Luz", data: [], borderColor: "#f1c40f", yAxisID: 'y1' }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        scales: { 
            y: { position: 'left', max: 100 }, 
            y1: { position: 'right', max: 100, grid: {drawOnChartArea: false} } 
        }
    }
});


// ===============================
// ACTUALIZACIÓN CONTROLADA
// ===============================

setInterval(() => {

    fetch("/datos")
    .then(res => res.json())
    .then(data => {

        // Si sistema apagado o desconectado
        if (data.estado === "SISTEMA APAGADO" || data.estado === "DESCONECTADO") {
            sistemaActivo = false;
            mostrarEstadoEspecial(data.estado);
            return;
        }

        sistemaActivo = true;

        // SOLO actualizar si hay cambio real
        let nuevoTimestamp = JSON.stringify(data);

        if (nuevoTimestamp === ultimoTimestamp) return;

        ultimoTimestamp = nuevoTimestamp;

        actualizarUI(data);
        evaluar("temp", data.temperatura, 18, 24);
        evaluar("humAir", data.humedad_aire, 60, 80);
        evaluar("humSoil", data.humedad_suelo, 65, 80);
        evaluar("lux", data.luminosidad, 60, 85);
        actualizarGrafica(data);
    });

}, 5000);


// ===============================
// ACTUALIZAR UI
// ===============================

function actualizarUI(data) {
    document.getElementById("temperatura").innerText = data.temperatura;
    document.getElementById("humedad_aire").innerText = data.humedad_aire;
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo;
    document.getElementById("luminosidad").innerText = data.luminosidad;
    document.getElementById("lux_p").innerText = data.luminosidad;
    document.getElementById("estado-sistema").innerText = "Estado: " + data.estado;
}


// ===============================
// EVALUACIÓN VISUAL
// ===============================

function evaluar(id, val, min, max) {
    const el = document.getElementById(id);
    el.className = (val >= min && val <= max) ? "card verde" : "card rojo";
}


// ===============================
// ESTADO ESPECIAL
// ===============================

function mostrarEstadoEspecial(estado) {

    const stTxt = document.getElementById("estado-sistema");
    const diag = document.getElementById("mensaje-adecuado");

    stTxt.innerText = estado;
    stTxt.style.color = (estado === "SISTEMA APAGADO") ? "#c0392b" : "gray";

    diag.innerText = estado;
    diag.className = "diagnostico-box";

    document.querySelectorAll("span").forEach(s => s.innerText = "--");
}


// ===============================
// ACTUALIZAR GRÁFICA OPTIMIZADA
// ===============================

function actualizarGrafica(d) {

    if (!sistemaActivo) return;

    if (miGrafica.data.labels.length > 12) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }

    miGrafica.data.labels.push(new Date().toLocaleTimeString());
    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.luminosidad);

    miGrafica.update();
}


// ===============================
// CONTROL SISTEMA
// ===============================

function controlSistema(accion) {

    fetch("/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: accion })
    });
}

