let ctx = document.getElementById("graficoMultivariable").getContext("2d");

let ultimoHash = "";

let miGrafica = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            { label: "Temp", data: [], borderColor: "#e74c3c", tension: 0.2 },
            { label: "H.Aire", data: [], borderColor: "#3498db", tension: 0.2 },
            { label: "H.Suelo", data: [], borderColor: "#e67e22", tension: 0.2 },
            { label: "Luz", data: [], borderColor: "#f1c40f", tension: 0.2 }
        ]
    },
    options: {
        animation: false,
        responsive: true,
        parsing: false,
        plugins: { legend: { display: true } },
        scales: {
            y: { beginAtZero: true, max: 100 }
        }
    }
});


// ===============================
// ACTUALIZACIÓN EFICIENTE
// ===============================

async function actualizar() {

    try {
        const res = await fetch("/datos");
        const data = await res.json();

        const hashActual = JSON.stringify(data);

        // 🔥 Si no hay cambios reales, no hacer nada
        if (hashActual === ultimoHash) return;

        ultimoHash = hashActual;

        // Estados especiales
        if (data.estado === "SISTEMA APAGADO" || data.estado === "DESCONECTADO") {
            mostrarEstadoEspecial(data.estado);
            return;
        }

        actualizarUI(data);
        actualizarGrafica(data);

    } catch (error) {
        console.log("Error fetch:", error);
    }
}


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
// GRÁFICA ULTRA LIGERA
// ===============================

function actualizarGrafica(d) {

    if (miGrafica.data.labels.length >= 8) {
        miGrafica.data.labels.shift();
        miGrafica.data.datasets.forEach(ds => ds.data.shift());
    }

    miGrafica.data.labels.push(new Date().toLocaleTimeString());

    miGrafica.data.datasets[0].data.push(d.temperatura);
    miGrafica.data.datasets[1].data.push(d.humedad_aire);
    miGrafica.data.datasets[2].data.push(d.humedad_suelo);
    miGrafica.data.datasets[3].data.push(d.luminosidad);

    miGrafica.update("none"); // 🔥 actualización sin animación
}


// ===============================
// ESTADO ESPECIAL
// ===============================

function mostrarEstadoEspecial(estado) {

    document.getElementById("estado-sistema").innerText = estado;

    document.querySelectorAll("span").forEach(s => s.innerText = "--");

    miGrafica.data.labels = [];
    miGrafica.data.datasets.forEach(ds => ds.data = []);
    miGrafica.update("none");
}


// ===============================
// BOTONES
// ===============================

function controlSistema(accion) {
    fetch("/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: accion })
    });
}


// ===============================
// INTERVALO CONTROLADO
// ===============================

setInterval(actualizar, 3000);
