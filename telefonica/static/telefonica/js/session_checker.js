/**
 * Script para verificar el estado de la sesión y redirigir al login si ha expirado
 * Este script se ejecuta periódicamente para comprobar si la sesión sigue activa
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Inicializando verificador de sesión");
    
    // Verificar la sesión cada minuto (60000 ms)
    setInterval(checkSession, 700000);
    
    // También verificar al cargar la página
    checkSession();
    
    // Función para verificar el estado de la sesión
    function checkSession() {
        fetch('/api/check-session/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            // Si la respuesta no es exitosa (por ejemplo, 401 o 403), redirigir al login
            if (!response.ok) {
                console.log("Sesión expirada, redirigiendo al login");
                window.location.href = '/login/';
                return;
            }
            
            return response.json();
        })
        .then(data => {
            if (data && !data.authenticated) {
                console.log("Usuario no autenticado, redirigiendo al login");
                window.location.href = '/login/';
            }
        })
        .catch(error => {
            console.error("Error al verificar la sesión:", error);
            // En caso de error, también redirigir al login por seguridad
            window.location.href = '/login/';
        });
    }
});