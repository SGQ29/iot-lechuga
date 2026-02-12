let ctx = document.getElementById("graficoMultivariable").getContext("2d");

let sistemaActivo = true;
let ultimoTimestamp = 0;

/* ===========================
   CONFIGURACIÓN GRÁFICA PRO
=========================== */

let miGrafica = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            {
                label: "Temp",
                data: [],
                borderColor: "#e74c3c",
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.2
            },
            {
                label: "H.Aire",
                data: [],
                borderColor: "#3498db",
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.2
            },
            {
                label: "H.Suelo",
                data: [],
                borderColor: "#e67e22",
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.2
            },
            {
                label: "Luz",
                data: [],
                borderColor: "#f1c40f",
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.2
            }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                max: 100
            }
        }
    }
});

/* ===========================
   ACTUALIZACIÓN EN TIEMPO REAL
=========================== */

setInterval(actualizar, 1000); // 1 segundo REAL TIME

async function actualizar() {

    if (!sistemaActivo) return;

    try {
        const res = await fetch("/datos");
        const data = await res.json();

        if (data.timestamp === ultimoTimestamp) return;
        ultimoTimestamp = data.timestamp;

        actualizarUI(data);
        actualizarGrafica(data);

    } catch (error) {
        console.log("Error:", error);
    }
}

/* ===========================
   ACTUALIZAR INTERFAZ
=========================== */

function actualizarUI(data) {

    document.getElementById("temperatura").innerText = data.temperatura.toFixed(1);
    document.getElementById("humedad_aire").innerText = data.humedad_aire.toFixed(1);
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo.toFixed(0);
    document.getElementById("luminosidad").innerText = data.luminosidad.toFixed(0);
    document.getElementById("lux_p").innerText = data.lux_p.toFixed(0);

    let alertas = [];

    // LIMPIAR COLORES
    limpiarEstado("temp");
    limpiarEstado("humAir");
    limpiarEstado("humSoil");
    limpiarEstado("lux");

    /* ===== RANGOS ÓPTIMOS LECHUGA CRESPA ===== */

    if (data.temperatura < 18 || data.temperatura > 24) {
        alertas.push("Temperatura");
        setRojo("temp");
    } else setVerde("temp");

    if (data.humedad_aire < 60 || data.humedad_aire > 80) {
        alertas.push("Humedad Aire");
        setRojo("humAir");
    } else setVerde("humAir");

    if (data.humedad_suelo < 65 || data.humedad_suelo > 80) {
        alertas.push("Humedad Suelo");
        setRojo("humSoil");
    } else setVerde("humSoil");

    if (data.lux_p < 30 || data.lux_p > 80) {
        alertas.push("Luminosidad");
        setRojo("lux");
    } else setVerde("lux");

    const box = document.getElementById("mensaje-adecuado");

    if (alertas.length === 0) {
        box.innerText = "✅ CULTIVO EN CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = "⚠ ALERTA: CONDICIONES NO ÓPTIMAS (" + alertas.join(", ") + ")";
        box.className = "diagnostico-box estado-alerta";
    }
}

/* ===========================
   ACTUALIZAR GRÁFICA
=========================== */

function actualizarGrafica(d) {

    if (miGrafica.data.labels.length > 20) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }

    miGrafica.data.labels.push(new Date().toLocaleTimeString());

    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.lux_p);

    miGrafica.update("none");
}

/* ===========================
   CONTROL SISTEMA
=========================== */

function controlSistema(accion) {

    if (accion === "apagar") {
        sistemaActivo = false;

        document.getElementById("estado-sistema").innerText = "Estado: SISTEMA APAGADO";

        document.querySelectorAll(".card").forEach(c => {
            c.classList.remove("verde");
            c.classList.add("rojo");
        });

        const box = document.getElementById("mensaje-adecuado");
        box.innerText = "🔴 SISTEMA APAGADO";
        box.className = "diagnostico-box estado-alerta";

    }

    if (accion === "encender") {
        sistemaActivo = true;
        document.getElementById("estado-sistema").innerText = "Estado: SISTEMA ENCENDIDO";
    }
}

/* ===========================
   FUNCIONES AUXILIARES
=========================== */

function setRojo(id) {
    document.getElementById(id).classList.add("rojo");
}

function setVerde(id) {
    document.getElementById(id).classList.add("verde");
}

function limpiarEstado(id) {
    let el = document.getElementById(id);
    el.classList.remove("rojo");
    el.classList.remove("verde");
}

