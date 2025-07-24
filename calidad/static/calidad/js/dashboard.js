document.addEventListener('DOMContentLoaded', function () {
    initCharts();
    initDateRangePicker();
    initThemeToggle();
});

function obtenerFiltrosActuales() {
    // Obtener valores de filtro desde el template (si existen)
    const fechaInicio = document.querySelector('meta[name="fecha-inicio"]')?.content;
    const fechaFin = document.querySelector('meta[name="fecha-fin"]')?.content;
    
    if (fechaInicio && fechaFin) {
        return {
            fechaInicio: new Date(fechaInicio + 'T00:00:00'),
            fechaFin: new Date(fechaFin + 'T00:00:00')
        };
    }
    return null;
}

function showNoDataMessage(canvas) {
    if (!canvas) return;
    const container = canvas.parentElement;
    if (!container) return;
    const p = document.createElement('p');
    p.className = 'text-center text-muted d-flex align-items-center justify-content-center h-100';
    p.innerHTML = '<i class="fas fa-info-circle me-2"></i>No hay datos disponibles.';
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    container.appendChild(p);
}

function parseChartData(element, attribute) {
    try {
        return JSON.parse(element.dataset[attribute] || '[]');
    } catch (e) {
        console.error(`Error parsing data from ${attribute}:`, e);
        return [];
    }
}

function initCharts() {
    // Gráfico 1: Top 5 Incumplimientos (Barra Horizontal)
    const ctxIncumplimientos = document.getElementById('topIncumplimientosChart');
    if (ctxIncumplimientos) {
        const labels = parseChartData(ctxIncumplimientos, 'labels');
        const data = parseChartData(ctxIncumplimientos, 'data');
        if (labels.length > 0) {
            new Chart(ctxIncumplimientos, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Nº de Incumplimientos',
                        data: data,
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        borderRadius: 4,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { 
                        x: { ticks: { precision: 0 } },
                        y: {
                            ticks: {
                                callback: function(value, index, values) {
                                    const label = this.getLabelForValue(value);
                                    if (label.length > 30) {
                                        // Dividir texto largo en múltiples líneas
                                        const words = label.split(' ');
                                        const lines = [];
                                        let currentLine = '';
                                        
                                        words.forEach(word => {
                                            if ((currentLine + word).length > 30) {
                                                if (currentLine) lines.push(currentLine.trim());
                                                currentLine = word + ' ';
                                            } else {
                                                currentLine += word + ' ';
                                            }
                                        });
                                        if (currentLine) lines.push(currentLine.trim());
                                        
                                        return lines;
                                    }
                                    return label;
                                },
                                maxRotation: 0,
                                minRotation: 0
                            }
                        }
                    }
                }
            });
        } else {
            showNoDataMessage(ctxIncumplimientos);
        }
    }

    // Gráfico 2: Distribución por Tipología (Dona)
    const ctxTipologias = document.getElementById('tipologiasChart');
    if (ctxTipologias) {
        const labels = parseChartData(ctxTipologias, 'labels');
        const values = parseChartData(ctxTipologias, 'values');
        if (labels.length > 0) {
            new Chart(ctxTipologias, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796'],
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        } else {
            showNoDataMessage(ctxTipologias);
        }
    }

    // Gráfico 3: Evolución de Puntuación (Línea)
    const ctxEvolucion = document.getElementById('evolucionChart');
    if (ctxEvolucion) {
        const labels = parseChartData(ctxEvolucion, 'labels');
        const dataManual = parseChartData(ctxEvolucion, 'manual');
        let dataIA = parseChartData(ctxEvolucion, 'ia');
        // Escalar valores de IA (speech) que vienen como decimales 0.xx a porcentaje 0-100
        dataIA = dataIA.map(v => (typeof v === 'number' && v <= 1 ? v * 100 : v));
        if (labels.length > 0) {
            new Chart(ctxEvolucion, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Manual', data: dataManual, borderColor: '#4e73df', tension: 0.3, fill: false },
                        { label: 'IA', data: dataIA, borderColor: '#1cc88a', tension: 0.3, fill: false }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: { y: { min: 0, max: 100, ticks: { callback: (value) => value + '%' } } }
                }
            });
        } else {
            showNoDataMessage(ctxEvolucion);
        }
    }
}

function initDateRangePicker() {
    console.log('Iniciando initDateRangePicker');
    const dateRangeEl = document.getElementById('dateRangePicker');
    const refreshBtn = document.getElementById('refreshBtn');
    
    console.log('dateRangeEl:', dateRangeEl);
    console.log('refreshBtn:', refreshBtn);
    console.log('flatpickr disponible:', typeof flatpickr !== 'undefined');
    
    if (dateRangeEl && typeof flatpickr !== 'undefined') {
        // Obtener filtros actuales para establecer valores iniciales
        const filtrosActuales = obtenerFiltrosActuales();
        const fechasIniciales = filtrosActuales ? [filtrosActuales.fechaInicio, filtrosActuales.fechaFin] : [];
        
        const fp = flatpickr(dateRangeEl, {
            mode: 'range',
            dateFormat: 'Y-m-d',
            maxDate: 'today',
            locale: 'es',
            placeholder: 'Seleccionar rango de fechas',
            defaultDate: fechasIniciales,
            onClose: function(selectedDates, dateStr) {
                if (selectedDates.length === 2) {
                    // Aplicar filtro automáticamente cuando se selecciona un rango
                    aplicarFiltroFechas(selectedDates[0], selectedDates[1]);
                } else if (selectedDates.length === 0) {
                    // Si se limpia el filtro, recargar sin filtros
                    aplicarFiltroFechas(null, null);
                }
            }
        });
        
        // Agregar botón para limpiar filtro
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-outline-secondary btn-sm ms-2';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.title = 'Limpiar filtro de fechas';
        clearBtn.onclick = function() {
            fp.clear();
            aplicarFiltroFechas(null, null);
        };
        dateRangeEl.parentNode.appendChild(clearBtn);
    }
    
    // Configurar botón de actualizar
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            console.log('Click en botón actualizar');
            // Obtener fechas actuales del picker si existen
            const currentDates = dateRangeEl._flatpickr ? dateRangeEl._flatpickr.selectedDates : [];
            console.log('Fechas actuales del picker:', currentDates);
            if (currentDates.length === 2) {
                aplicarFiltroFechas(currentDates[0], currentDates[1]);
            } else {
                aplicarFiltroFechas(null, null);
            }
        });
    } else {
        console.log('No se encontró el botón refreshBtn');
    }
}

function aplicarFiltroFechas(fechaInicio, fechaFin) {
    console.log('Aplicando filtro de fechas:', fechaInicio, fechaFin);
    const loadingIndicator = document.getElementById('loadingIndicator');
    const mainContent = document.querySelector('.container-fluid > .row');
    
    // Mostrar indicador de carga
    if (loadingIndicator) {
        loadingIndicator.classList.remove('d-none');
    }
    
    // Ocultar contenido principal temporalmente
    if (mainContent) {
        mainContent.style.opacity = '0.5';
    }
    
    // Construir URL con parámetros de filtro
    const url = new URL(window.location.href);
    
    if (fechaInicio && fechaFin) {
        url.searchParams.set('fecha_inicio', formatearFecha(fechaInicio));
        url.searchParams.set('fecha_fin', formatearFecha(fechaFin));
    } else {
        url.searchParams.delete('fecha_inicio');
        url.searchParams.delete('fecha_fin');
    }
    
    // Recargar la página con los nuevos parámetros
    window.location.href = url.toString();
}

function formatearFecha(fecha) {
    // Formatear fecha como YYYY-MM-DD para el backend
    const year = fecha.getFullYear();
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const day = String(fecha.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        themeToggle.checked = savedTheme === 'dark';
        themeToggle.addEventListener('change', function () {
            const theme = this.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        });
    }
}
