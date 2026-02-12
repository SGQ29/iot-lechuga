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
        scales: { 
            y: { position: 'left', max: 100 }, 
            y1: { position: 'right', max: 1000, grid: {drawOnChartArea: false} } 
        }
    }
});

setInterval(() => {
    if (!sistemaActivo) return;
    fetch("/datos").then(res => res.json()).then(data => {
        if (data.temperatura === null) return;

        // Actualizar UI
        document.getElementById("temperatura").innerText = data.temperatura;
        document.getElementById("humedad_aire").innerText = data.humedad_aire;
        document.getElementById("humedad_suelo").innerText = data.humedad_suelo;
        document.getElementById("luminosidad").innerText = data.luminosidad;
        document.getElementById("lux_p").innerText = data.lux_p;

        // Evaluar colores individuales
        evaluar("temp", data.temperatura, 15, 18);
        evaluar("humAir", data.humedad_aire, 60, 80);
        evaluar("humSoil", data.humedad_suelo, 70, 80);
        evaluar("lux", data.luminosidad, 400, 600);

        // Diagnóstico de Cultivo
        verificarCultivo(data);
        
        // Actualizar Gráfica
        actualizarGrafica(data);
    });
}, 1000);

function evaluar(id, val, min, max) {
    const el = document.getElementById(id);
    el.className = (val >= min && val <= max) ? "card verde" : "card rojo";
}

function verificarCultivo(data) {
    const box = document.getElementById("mensaje-adecuado");
    let causa = "";
    if (data.temperatura < 15 || data.temperatura > 18) causa = "Temperatura";
    else if (data.humedad_aire < 60 || data.humedad_aire > 80) causa = "Hum. Aire";
    else if (data.humedad_suelo < 70 || data.humedad_suelo > 80) causa = "Hum. Suelo";
    else if (data.luminosidad < 400 || data.luminosidad > 600) causa = "Luz";

    if (causa === "") {
        box.innerText = "✅ CULTIVO ADECUADO: CONDICIONES ÓPTIMAS";
        box.className = "diagnostico-box estado-adecuado";
    } else {
        box.innerText = `⚠️ ALERTA: CONDICIONES NO ÓPTIMAS (${causa})`;
        box.className = "diagnostico-box estado-alerta";
    }
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
    miGrafica.update();
}

function controlSistema(estado) {
    fetch(`/control/${estado}`);
    const stTxt = document.getElementById("estado-sistema");
    const diag = document.getElementById("mensaje-adecuado");
    
    if (estado === 'on') {
        sistemaActivo = true;
        stTxt.innerText = "SISTEMA OPERANDO NORMALMENTE: RECIBIENDO DATOS";
        stTxt.style.color = "#27ae60";
    } else {
        sistemaActivo = false;
        stTxt.innerText = "SISTEMA APAGADO";
        stTxt.style.color = "#c0392b";
        diag.innerText = "SISTEMA FUERA DE LÍNEA";
        diag.className = "diagnostico-box";
        document.querySelectorAll("span").forEach(s => s.innerText = "--");
    }
}
