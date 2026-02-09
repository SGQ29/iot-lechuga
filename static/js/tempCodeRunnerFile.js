let sistemaEncendido = true;

setInterval(() => {
    if (!sistemaEncendido) return;

    fetch("/datos")
        .then(r => r.json())
        .then(data => {
            if (data.temperatura === null) return;

            document.getElementById("temperatura").innerText = data.temperatura.toFixed(1);
            document.getElementById("humedad_aire").innerText = data.humedad_aire.toFixed(1);
            document.getElementById("humedad_suelo").innerText = data.humedad_suelo;
            document.getElementById("luminosidad").innerText = data.luminosidad;

            evaluar("temp", data.temperatura, 15, 18);
            evaluar("humAir", data.humedad_aire, 60, 80);
            evaluar("humSoil", data.humedad_suelo, 70, 80);
            evaluar("lux", data.luminosidad, 400, 600);

            document.getElementById("estado").innerText = "Estado: " + data.estado;
        });
}, 1000);

function evaluar(id, valor, min, max) {
    const card = document.getElementById(id);
    card.className = "card";

    if (valor >= min && valor <= max) card.classList.add("verde");
    else card.classList.add("rojo");
}

function encender() {
    fetch("/control/on");
    sistemaEncendido = true;
}

function apagar() {
    fetch("/control/off");
    sistemaEncendido = false;
}
