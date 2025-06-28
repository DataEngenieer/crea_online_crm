// Funciones JS básicas para el chat modal
function toggleChatModal() {
    const modal = document.getElementById('chat-modal');
    const fab = document.getElementById('chat-fab');
    if (modal.style.display === 'none' || modal.style.display === '') {
        modal.style.display = 'block';
        fab.style.display = 'none';
        cargarMensajes();
    } else {
        modal.style.display = 'none';
        fab.style.display = 'block';
    }
}

function cargarMensajes() {
    fetch('/chat/mensajes/')
        .then(response => response.json())
        .then(data => {
            const mensajes = data.mensajes || [];
            const contenedor = document.getElementById('chat-messages');
            contenedor.innerHTML = '';
            mensajes.forEach(msg => {
                const div = document.createElement('div');
                div.className = 'mb-1';
                div.innerHTML = `<strong>${msg.remitente}</strong>: ${msg.mensaje} <small class='text-muted'>${msg.timestamp}</small>`;
                contenedor.appendChild(div);
            });
            contenedor.scrollTop = contenedor.scrollHeight;
        });
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('chat-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const mensaje = input.value.trim();
        // Si existe el select de destinatario, es supervisor
        const selectDest = document.getElementById('chat-destinatario');
        let destinatario_id = null;
        if (selectDest) {
            destinatario_id = selectDest.value;
            if (!destinatario_id) {
                alert('Selecciona un asesor antes de enviar el mensaje.');
                return;
            }
        }
        if (mensaje.length === 0) return;
        let bodyData = {mensaje: mensaje};
        if (destinatario_id) {
            bodyData.destinatario_id = destinatario_id;
        }
        fetch('/chat/enviar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(bodyData)
        }).then(() => {
            input.value = '';
            cargarMensajes();
        });
    });
});

function enviarMasivo() {
    const mensaje = prompt('Mensaje masivo a todos los asesores:');
    if (!mensaje) return;
    fetch('/chat/masivo/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({mensaje: mensaje})
    }).then(() => {
        cargarMensajes();
    });
}

function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const c = cookies[i].trim();
        if (c.startsWith('csrftoken=')) {
            return c.substring('csrftoken='.length, c.length);
        }
    }
    return '';
}
// Opcional: setInterval para refrescar mensajes cada X segundos
setInterval(cargarMensajes, 10000);
