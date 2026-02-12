let ctx = document.getElementById("graficoMultivariable").getContext("2d");
let sistemaActivo = false;   // INICIA APAGADO

let miGrafica = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "Temp", data: [], borderColor: "#e74c3c", yAxisID: 'y', tension: 0.2, pointRadius: 2 },
            { label: "H.Aire", data: [], borderColor: "#3498db", yAxisID: 'y', tension: 0.2, pointRadius: 2 },
            { label: "H.Suelo", data: [], borderColor: "#e67e22", yAxisID: 'y', tension: 0.2, pointRadius: 2 },
            { label: "Luz", data: [], borderColor: "#f1c40f", yAxisID: 'y1', tension: 0.2, pointRadius: 2 }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: { 
            y: { position: 'left', max: 100 }, 
            y1: { position: 'right', max: 1000, grid: {drawOnChartArea: false} } 
        }
    }
});

/* =========================
   ACTUALIZACIÓN AUTOMÁTICA
========================= */

setInterval(() => {

    if (!sistemaActivo) return;

    fetch("/datos")
    .then(res => res.json())
    .then(data => {

        if (!data || data.temperatura === null) return;

        actualizarUI(data);
        actualizarGrafica(data);
    });

}, 1000);


/* =========================
   ACTUALIZAR UI
========================= */

function actualizarUI(data) {

    document.getElementById("temperatura").innerText = data.temperatura.toFixed(1);
    document.getElementById("humedad_aire").innerText = data.humedad_aire.toFixed(1);
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo.toFixed(0);
    document.getElementById("luminosidad").innerText = data.luminosidad.toFixed(0);
    document.getElementById("lux_p").innerText = data.lux_p.toFixed(0);

    evaluar("temp", data.temperatura, 18, 24);
    evaluar("humAir", data.humedad_aire, 60, 80);
    evaluar("humSoil", data.humedad_suelo, 65, 80);
    evaluar("lux", data.luminosidad, 400, 600);

    verificarCultivo(data);
}


/* =========================
   EVALUAR RANGOS
========================= */

function evaluar(id, val, min, max) {

    const el = document.getElementById(id);

    if (val >= min && val <= max) {
        el.className = "card verde";
    } else {
        el.className = "card rojo";
    }
}


/* =========================
   DIAGNÓSTICO
========================= */

function verificarCultivo(data) {

    const box = document.getElementById("mensaje-adecuado");

    let alertas = [];

    if (data.temperatura < 18 || data.temperatura > 24)
        alertas.push("Temperatura");

    if (data.humedad_aire < 60 || data.humedad_aire > 80)
        alertas.push("Humedad Aire");

    if (data.humedad_suelo < 65 || data.humedad_suelo > 80)
        alertas.push("Humedad Suelo");

    if (data.luminosidad < 400 || data.luminosidad > 600)
        alertas.push("Luminosidad");

    if (alertas.length === 0) {
        box.innerText = "✅ CULTIVO ADECUADO: CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = "⚠️ ALERTA: CONDICIONES NO ÓPTIMAS (" + alertas.join(", ") + ")";
        box.className = "diagnostico-box estado-alerta";
    }
}


/* =========================
   GRÁFICA
========================= */

function actualizarGrafica(d) {

    if (miGrafica.data.labels.length > 20) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }

    miGrafica.data.labels.push(new Date().toLocaleTimeString());

    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.luminosidad);

    miGrafica.update("none");
}


/* =========================
   BOTONES ON / OFF
========================= */

function controlSistema(estado) {

    fetch(`/control/${estado}`);

    const stTxt = document.getElementById("estado-sistema");
    const diag = document.getElementById("mensaje-adecuado");

    if (estado === 'on') {

        sistemaActivo = true;

        stTxt.innerText = "SISTEMA OPERANDO NORMALMENTE";
        stTxt.style.color = "#27ae60";

    } else {

        sistemaActivo = false;

        stTxt.innerText = "SISTEMA APAGADO";
        stTxt.style.color = "#c0392b";

        // LIMPIAR DATOS VISUALES
        document.querySelectorAll("span").forEach(s => s.innerText = "--");

        diag.innerText = "SISTEMA FUERA DE LÍNEA";
        diag.className = "diagnostico-box";

        // LIMPIAR GRÁFICA
        miGrafica.data.labels = [];
        miGrafica.data.datasets.forEach(ds => ds.data = []);
        miGrafica.update();
    }
}
