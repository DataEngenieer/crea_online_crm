// Archivo responsive.js para evitar errores 404
// JavaScript para funcionalidades responsivas básicas

document.addEventListener('DOMContentLoaded', function() {
    // Función para manejar el redimensionamiento de ventana
    function handleResize() {
        const width = window.innerWidth;
        
        // Ajustar elementos según el tamaño de pantalla
        if (width < 768) {
            // Móvil
            document.body.classList.add('mobile-view');
            document.body.classList.remove('desktop-view');
        } else {
            // Desktop
            document.body.classList.add('desktop-view');
            document.body.classList.remove('mobile-view');
        }
    }
    
    // Ejecutar al cargar la página
    handleResize();
    
    // Ejecutar cuando se redimensiona la ventana
    window.addEventListener('resize', handleResize);
    
    // Mejorar la experiencia en dispositivos táctiles
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
    }
});