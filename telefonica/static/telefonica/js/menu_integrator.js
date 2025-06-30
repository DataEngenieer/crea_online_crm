/**
 * Script para integrar el menú de Telefónica en la navegación lateral
 */
document.addEventListener('DOMContentLoaded', function() {
    // Buscamos el contenedor de la lista de navegación
    const listGroup = document.querySelector('.list-group.list-group-flush.flex-grow-1');
    
    if (listGroup) {
        // Cargar el fragmento de menú desde el servidor
        fetch('/telefonica/menu/')
            .then(response => response.text())
            .then(html => {
                // Convertir el HTML en un elemento del DOM
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                const menuItem = tempDiv.firstElementChild;
                
                // Verificar si se ha obtenido un elemento de menú válido
                if (menuItem) {
                    // Punto de inserción: después del último elemento existente
                    listGroup.appendChild(menuItem);
                    
                    // Activar el elemento si estamos en una sección de Telefónica
                    const currentPath = window.location.pathname;
                    if (currentPath.startsWith('/telefonica/')) {
                        // Resaltar el menú de Telefónica
                        const telefonicaMenu = document.getElementById('sidebarTelefonica');
                        if (telefonicaMenu) {
                            telefonicaMenu.classList.add('active');
                            
                            // Expandir el submenú
                            const collapseMenu = document.getElementById('collapseTelefonica');
                            if (collapseMenu) {
                                collapseMenu.classList.add('show');
                            }
                            
                            // Activar el enlace específico según la ruta actual
                            if (currentPath.includes('dashboard')) {
                                document.getElementById('dashboardLink')?.classList.add('active');
                            } else if (currentPath.includes('venta/crear')) {
                                document.getElementById('crearVentaLink')?.classList.add('active');
                            } else if (currentPath.includes('ventas/lista')) {
                                document.getElementById('ventasListaLink')?.classList.add('active');
                            } else if (currentPath.includes('ventas/devueltas')) {
                                document.getElementById('devueltasLink')?.classList.add('active');
                            } else if (currentPath.includes('ventas/pendientes')) {
                                document.getElementById('pendientesLink')?.classList.add('active');
                            } else if (currentPath.includes('ventas/digitacion')) {
                                document.getElementById('digitacionLink')?.classList.add('active');
                            } else if (currentPath.includes('ventas/seguimiento')) {
                                document.getElementById('seguimientoLink')?.classList.add('active');
                            } else if (currentPath.includes('comisiones')) {
                                document.getElementById('comisionesLink')?.classList.add('active');
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error al cargar el menú de Telefónica:', error);
            });
    }
});