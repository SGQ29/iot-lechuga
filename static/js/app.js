let ctx = document.getElementById("graficoMultivariable").getContext("2d");

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
            y: { beginAtZero: true, max: 100 }
        }
    }
});

let ultimoTimestamp = 0;

async function actualizar() {
    try {
        const res = await fetch("/datos");
        const data = await res.json();

        if (data.timestamp === ultimoTimestamp) {
            setTimeout(actualizar, 2000);
            return;
        }

        ultimoTimestamp = data.timestamp;

        actualizarUI(data);
        actualizarGrafica(data);

    } catch (error) {
        console.log(error);
    }

    setTimeout(actualizar, 2000);
}

actualizar();

function actualizarUI(data) {
    document.getElementById("temperatura").innerText = data.temperatura;
    document.getElementById("humedad_aire").innerText = data.humedad_aire;
    document.getElementById("humedad_suelo").innerText = data.humedad_suelo;
    document.getElementById("luminosidad").innerText = data.luminosidad;
    document.getElementById("lux_p").innerText = data.lux_p;
    document.getElementById("estado-sistema").innerText = data.estado;
}

function actualizarGrafica(d) {
    if (miGrafica.data.labels.length > 15) {
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
