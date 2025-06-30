/**
 * Script general para el módulo de Telefónica
 * Contiene funciones comunes para todas las páginas del módulo
 */

// Ejecutar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log("Módulo Telefónica inicializado");
    
    // Inicializar tooltips de Bootstrap 5
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers de Bootstrap 5
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Primero verificamos que jQuery esté disponible
    if (typeof jQuery !== 'undefined') {
        // Configuración para dataTables (si están presentes)
        if (typeof jQuery.fn.DataTable !== 'undefined') {
            jQuery('.datatable').DataTable({
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.13.2/i18n/es-ES.json'
                }
            });
        }
    }
});
