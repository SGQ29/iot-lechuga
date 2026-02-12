let ctx = document.getElementById("graficoMultivariable").getContext("2d");
let sistemaActivo = true;

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
        scales: { 
            y: { position: 'left', max: 100 }, 
            y1: { position: 'right', max: 100, grid: {drawOnChartArea: false} } 
        }
    }
});


// ==========================
// ACTUALIZACIÓN EN TIEMPO REAL
// ==========================

setInterval(() => {

    fetch("/datos")
    .then(res => res.json())
    .then(data => {

        // ===== SI SISTEMA APAGADO =====
        if (data.estado === "SISTEMA APAGADO") {
            sistemaActivo = false;
            mostrarApagado();
            return;
        }

        // ===== SI DESCONECTADO =====
        if (data.estado === "DESCONECTADO") {
            sistemaActivo = false;
            mostrarDesconectado();
            return;
        }

        sistemaActivo = true;

        // ===== ACTUALIZAR UI =====
        document.getElementById("temperatura").innerText = data.temperatura;
        document.getElementById("humedad_aire").innerText = data.humedad_aire;
        document.getElementById("humedad_suelo").innerText = data.humedad_suelo;
        document.getElementById("luminosidad").innerText = data.luminosidad;
        document.getElementById("lux_p").innerText = data.luminosidad;

        document.getElementById("estado-sistema").innerText = "Estado: " + data.estado;

        // ===== RANGOS ÓPTIMOS LECHUGA CRESPA =====
        evaluar("temp", data.temperatura, 18, 24);
        evaluar("humAir", data.humedad_aire, 60, 80);
        evaluar("humSoil", data.humedad_suelo, 65, 80);
        evaluar("lux", data.luminosidad, 60, 85);

        verificarCultivo(data);

        actualizarGrafica(data);
    });

}, 3000);


// ==========================
// EVALUAR TARJETAS
// ==========================

function evaluar(id, val, min, max) {
    const el = document.getElementById(id);

    if (val >= min && val <= max) {
        el.className = "card verde";
    } else {
        el.className = "card rojo";
    }
}


// ==========================
// DIAGNÓSTICO GENERAL
// ==========================

function verificarCultivo(data) {

    const box = document.getElementById("mensaje-adecuado");

    if (data.estado === "ÓPTIMO") {
        box.innerText = "✅ CULTIVO ADECUADO: CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    }
    else if (data.estado.includes("ALERTA")) {
        box.innerText = "⚠ ALERTA: " + data.estado;
        box.className = "diagnostico-box estado-alerta";
    }
}


// ==========================
// MOSTRAR APAGADO
// ==========================

function mostrarApagado() {

    const stTxt = document.getElementById("estado-sistema");
    const diag = document.getElementById("mensaje-adecuado");

    stTxt.innerText = "SISTEMA APAGADO";
    stTxt.style.color = "#c0392b";

    diag.innerText = "🔴 SISTEMA FUERA DE LÍNEA";
    diag.className = "diagnostico-box";

    document.querySelectorAll("span").forEach(s => s.innerText = "--");

    document.querySelectorAll(".card").forEach(c => c.className = "card rojo");
}


// ==========================
// MOSTRAR DESCONECTADO
// ==========================

function mostrarDesconectado() {

    const stTxt = document.getElementById("estado-sistema");
    const diag = document.getElementById("mensaje-adecuado");

    stTxt.innerText = "SISTEMA DESCONECTADO";
    stTxt.style.color = "gray";

    diag.innerText = "⚡ NO SE RECIBEN DATOS DEL ESP32";
    diag.className = "diagnostico-box";

    document.querySelectorAll(".card").forEach(c => c.className = "card rojo");
}


// ==========================
// ACTUALIZAR GRÁFICA
// ==========================

function actualizarGrafica(d) {

    if (!sistemaActivo) return;

    if (miGrafica.data.labels.length > 15) {
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


// ==========================
// CONTROL SISTEMA (BOTONES)
// ==========================

function controlSistema(accion) {

    fetch("/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: accion })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Sistema:", data);
    });
}
