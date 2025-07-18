/**
 * Script para el formulario de ventas con pestañas
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM completamente cargado y analizado");
    console.log("jQuery está disponible: " + (typeof jQuery !== 'undefined'));
    console.log("Bootstrap está disponible: " + (typeof bootstrap !== 'undefined'));
    
    // Función auxiliar para mostrar notificaciones con o sin toastr
    function mostrarNotificacion(tipo, mensaje) {
        if (typeof toastr !== 'undefined') {
            // Si toastr está disponible, usarlo
            toastr[tipo](mensaje);
        } else {
            // Alternativa: mostrar un alert o una notificación personalizada
            if (tipo === 'error') {
                alert('Error: ' + mensaje);
            } else {
                alert(mensaje);
            }
            // También podríamos crear una notificación Bootstrap
            // o cualquier otra alternativa si fuera necesario
        }
    }
    
    // Hacer la función disponible globalmente para el script
    window.mostrarNotificacion = mostrarNotificacion;
    
    // Inicializar el formulario con el botón de guardar deshabilitado por defecto
    $("#btn-guardar-venta").prop("disabled", true);
    
    // Verificar que las pestañas existen en el DOM
    console.log("Pestañas disponibles: " + $("#ventaTabs").length);
    $("#ventaTabs a").each(function() {
        console.log("Pestaña encontrada: " + $(this).attr("data-bs-target"));
    });
    
    // Escuchar eventos de cambio de pestaña para actualizar el estado visual
    // En Bootstrap 5, el evento es 'shown.bs.tab'
    $("#ventaTabs a").on('shown.bs.tab', function(e) {
        // En Bootstrap 5 debemos usar data-bs-target en lugar de href
        const activeTabId = $(e.target).attr('data-bs-target').substring(1);
        console.log("Pestaña activada mediante evento: " + activeTabId);
        updateStepIndicator(activeTabId);
        
        // Si estamos en la última pestaña, actualizar el resumen
        if (activeTabId === "confirmar") {
            console.log("Actualizando resumen por cambio de pestaña");
            actualizarResumen();
            actualizarResumenDocumentos();
        }
    });
    
    // Configurar navegación entre pestañas con botones Siguiente y Anterior
    $(".next-step").click(function() {
        // Obtener el ID de la pestaña actual y siguiente
        const currentTabId = $(this).closest(".tab-pane").attr("id");
        const nextTab = $(this).data("next");
        
        console.log("Intentando avanzar de " + currentTabId + " a " + nextTab);
        
        // Validar campos antes de avanzar
        if (validarCampos(currentTabId)) {
            console.log("Validación exitosa, avanzando a pestaña: " + nextTab);
            activateTab(nextTab);
        } else {
            console.log("Validación fallida, permaneciendo en pestaña actual");
        }
    });
    
    $(".prev-step").click(function() {
        const prevTab = $(this).data("prev");
        console.log("Yendo a pestaña anterior: " + prevTab);
        activateTab(prevTab);
    });
    
    // Función para actualizar el indicador visual de pasos
    function updateStepIndicator(tabId) {
        // Determinar el número de paso basado en la pestaña activa
        let stepNumber = 1;
        if (tabId === "venta") stepNumber = 2;
        if (tabId === "documento") stepNumber = 3;
        if (tabId === "confirmar") stepNumber = 4;
        
        // Actualizar puntos de pasos
        $(".step-dot").removeClass("active");
        $(".step-dot[data-step='" + stepNumber + "']").addClass("active");
        $("#current-step").text(stepNumber);
        
        console.log("Indicador actualizado a paso " + stepNumber);
    }
    
    // Función para activar una pestaña
    function activateTab(tabId) {
        try {
            console.log("Activando pestaña: " + tabId);
            
            // Obtener el elemento de la pestaña para activar (usando data-bs-target en Bootstrap 5)
            const tabElement = document.querySelector('#ventaTabs a[data-bs-target="#' + tabId + '"]');
            console.log("Elemento de pestaña encontrado: " + (tabElement !== null));
            
            if (!tabElement) {
                console.error("No se encontró la pestaña con ID: " + tabId);
                return;
            }
            
            // En Bootstrap 5, usamos la API de tab de forma diferente
            const tab = new bootstrap.Tab(tabElement);
            tab.show();
            
            console.log("Pestaña " + tabId + " activada con éxito");
            
            // Actualizar manualmente el indicador de pasos
            updateStepIndicator(tabId);
            
            // IMPORTANTE: Si estamos en la pestaña de confirmación, actualizar el resumen
            // con un pequeño retraso para asegurarnos de que la pestaña ya está visible
            if (tabId === "confirmar") {
                setTimeout(function() {
                    console.log("Actualizando resumen para confirmación");
                    actualizarResumen();
                    actualizarResumenDocumentos();
                    // Verificar si los datos se actualizaron correctamente
                    console.log("Nombre en resumen: " + $("#resumen-nombre").text());
                    console.log("Documento en resumen: " + $("#resumen-documento").text());
                }, 200);
            }
        } catch (error) {
            console.error("Error al activar la pestaña " + tabId + ": " + error.message);
        }
    }
    
    // Función para validar campos requeridos en cada pestaña
    function validarCampos(tabId) {
        console.log("Validando campos de la pestaña: " + tabId);
        let isValid = true;
        
        // Quitar estilo de error de todos los campos en esta pestaña
        $("#" + tabId + " .form-control").removeClass("is-invalid");
        $("#" + tabId + " .form-select").removeClass("is-invalid");
        
        // Validación específica para cada pestaña
        if (tabId === "cliente") {
            // Validar campos del cliente
            const camposRequeridos = [
                "id_tipo_documento", "id_documento", "id_nombre_completo", 
                "id_direccion", "id_ciudad", 
                "id_departamento", "id_telefono"
            ];
            
            camposRequeridos.forEach(function(campo) {
                const $campo = $("#" + campo);
                if (!$campo.val()) {
                    $campo.addClass("is-invalid");
                    isValid = false;
                    console.log("Campo inválido: " + campo);
                }
            });
        } else if (tabId === "venta") {
            // Validar campos de la venta
            const camposRequeridos = [
                "id_segmento", "id_tipo_cliente", "id_plan_adquiere", 
                "id_numero_contacto"
            ];
            
            camposRequeridos.forEach(function(campo) {
                const $campo = $("#" + campo);
                if (!$campo.val()) {
                    $campo.addClass("is-invalid");
                    isValid = false;
                    console.log("Campo inválido: " + campo);
                }
            });
        } else if (tabId === "documento") {
            // Validar documentos (al menos uno debería estar presente)
            const tieneDocumentos = $("#documento-list .documento-item").length > 0;
            if (!tieneDocumentos) {
                mostrarNotificacion('warning', 'Debe subir al menos un documento');
                isValid = false;
            }
        }
        
        if (!isValid) {
            mostrarNotificacion('error', 'Por favor complete todos los campos requeridos');
        }
        
        return isValid;
    }
    
    // Buscar cliente por documento
    $("#buscarCliente").click(function() {
        var tipo_documento = $("#id_tipo_documento").val();
        var documento = $("#id_documento").val();
        
        if (!documento) {
            mostrarNotificacion('warning', 'Debe ingresar un número de documento para buscar');
            return;
        }
        
        // Mostrar indicador de carga
        $("#buscarCliente").prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Buscando...');
        
        $.ajax({
            url: buscarClienteUrl,  // Esta variable debe estar definida en la plantilla
            data: {
                'tipo_documento': tipo_documento,
                'documento': documento
            },
            dataType: 'json',
            success: function(data) {
                if (data.found) {
                    // Si se encuentra el cliente, se cargan todos sus datos
                    $("#id_tipo_documento").val(data.tipo_documento);
                    $("#id_documento").val(data.documento);
                    $("#id_nombre_completo").val(data.nombre_completo);
                    $("#id_correo").val(data.correo);
                    $("#id_departamento").val(data.departamento);
                    $("#id_ciudad").val(data.ciudad);
                    $("#id_barrio").val(data.barrio);
                    $("#id_direccion").val(data.direccion);
                    $("#id_telefono").val(data.telefono);
                    
                    // Notificar al usuario
                    mostrarNotificacion('success', 'Cliente encontrado y datos cargados');
                    
                    // Resaltar los campos que fueron rellenados
                    $(".form-control, .form-select").addClass("bg-light").delay(1500).queue(function(next){
                        $(this).removeClass("bg-light");
                        next();
                    });
                } else {
                    // No se encontró el cliente, se dejan los campos vacíos para que se complete
                    mostrarNotificacion('info', 'Cliente no encontrado. Por favor complete los datos');
                }
            },
            error: function() {
                mostrarNotificacion('error', 'Error al buscar el cliente');
            },
            complete: function() {
                // Restaurar el estado normal del botón de búsqueda
                $("#buscarCliente").prop('disabled', false).html('Buscar');
            }
        });
    });
    
    // Manejar inputs de tipo file para mostrar el nombre del archivo seleccionado
    $(".custom-file-input").on("change", function() {
        let fileName = $(this).val().split("\\").pop();
        
        // Si es un input múltiple, mostrar el número de archivos seleccionados
        if ($(this).attr("multiple")) {
            let fileCount = this.files.length;
            if (fileCount > 1) {
                fileName = fileCount + " archivos seleccionados";
            }
        }
        
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
        
        // Actualizar la lista de documentos en el resumen
        actualizarResumenDocumentos();
    });
    
    // Función para actualizar los badges del resumen de documentos
    function actualizarResumenDocumentos() {
        console.log("Actualizando resumen de documentos...");
        
        // Verificar si hay archivos cargados en cada input de forma segura
        // Verificar primero si los elementos existen antes de intentar acceder a sus propiedades
        let docIdentidad = false;
        let contrato = false;
        let confronta = false;
        
        const docIdentidadEl = document.getElementById("id_documento_identidad");
        const contratoEl = document.getElementById("id_contrato_firmado");
        const confrontaEl = document.getElementById("id_confronta");
        
        // Comprobar cada elemento de manera segura
        if (docIdentidadEl && docIdentidadEl.files) {
            docIdentidad = docIdentidadEl.files.length > 0;
        }
        
        if (contratoEl && contratoEl.files) {
            contrato = contratoEl.files.length > 0;
        }
        
        if (confrontaEl && confrontaEl.files) {
            confronta = confrontaEl.files.length > 0;
        }
        
        console.log("Estado de documentos - Identidad: " + docIdentidad + ", Contrato: " + contrato + ", Confronta: " + confronta);
        
        // Actualizar los badges en el resumen utilizando clases de Bootstrap 5
        // También verificamos que los elementos del DOM existan antes de intentar actualizarlos
        if ($("#doc-identidad-badge").length) {
            $("#doc-identidad-badge")
                .text(docIdentidad ? "Cargado" : "No cargado")
                .removeClass("bg-success bg-secondary")
                .addClass(docIdentidad ? "bg-success" : "bg-secondary");
        }
        
        if ($("#contrato-badge").length) {
            $("#contrato-badge")
                .text(contrato ? "Cargado" : "No cargado")
                .removeClass("bg-success bg-secondary")
                .addClass(contrato ? "bg-success" : "bg-secondary");
        }
        
        if ($("#confronta-badge").length) {
            $("#confronta-badge")
                .text(confronta ? "Cargado" : "No cargado")
                .removeClass("bg-success bg-secondary")
                .addClass(confronta ? "bg-success" : "bg-secondary");
        }
    }
    
    // Habilitar/deshabilitar botón de guardar según el checkbox de confirmación
    $("#confirmo_venta").change(function() {
        $("#btn-guardar-venta").prop("disabled", !this.checked);
    });
    
    // Función para actualizar el resumen
    function actualizarResumen() {
        console.log("Ejecutando actualizarResumen()");
        // Actualizar datos del cliente
        $("#resumen-nombre").text($("#id_nombre_completo").val());
        
        // Actualizar documento con tipo
        const tipoDocVal = $("#id_tipo_documento").val();
        const docVal = $("#id_documento").val();
        $("#resumen-documento").text(tipoDocVal + ': ' + docVal);
        
        $("#resumen-telefono").text($("#id_telefono").val());
        $("#resumen-email").text($("#id_correo").val() || "No proporcionado");
        $("#resumen-direccion").text($("#id_direccion").val());
        $("#resumen-ciudad").text($("#id_ciudad").val() + ", " + $("#id_departamento").val());
        
        // Actualizar datos de la venta
        const tipoCliente = $("#id_tipo_cliente").val();
        const segmento = $("#id_segmento").val();
        
        if (tipoCliente) {
            const tipoClienteTexto = $("#id_tipo_cliente option:selected").text();
            $("#resumen-tipo-cliente").text(tipoClienteTexto);
        } else {
            $("#resumen-tipo-cliente").text("No seleccionado");
        }
        
        if (segmento) {
            const segmentoTexto = $("#id_segmento option:selected").text();
            $("#resumen-segmento").text(segmentoTexto);
        } else {
            $("#resumen-segmento").text("No seleccionado");
        }
        
        $("#resumen-plan").text($("#id_plan_adquiere").val() || "No especificado");
        $("#resumen-numero-contacto").text($("#id_numero_contacto").val() || "No especificado");
        
        // Mostrar u ocultar NIP e IMEI según corresponda
        if (tipoCliente === "existente" && segmento === "movil" && $("#id_nip").val()) {
            $("#resumen-nip-container").show();
            $("#resumen-nip").text($("#id_nip").val());
        } else {
            $("#resumen-nip-container").hide();
        }
        
        if (tipoCliente === "nuevo" && segmento === "movil" && $("#id_imei").val()) {
            $("#resumen-imei-container").show();
            $("#resumen-imei").text($("#id_imei").val());
        } else {
            $("#resumen-imei-container").hide();
        }
        
        // Actualizar el estado de los documentos
        actualizarResumenDocumentos();
        // cuando implementemos esa parte del formulario
    }
    
    // Validación básica de campos
    function validarCampos(paso) {
        let camposValidos = true;
        
        // Limpiar mensajes de error previos
        $(".invalid-feedback").hide();
        $(".form-control, .custom-file-input").removeClass("is-invalid");
        
        if (paso === "cliente") {
            // Validar campos de la pestaña cliente
            if (!$("#id_documento").val()) {
                $("#documento-error").text("El documento es requerido").show();
                $("#id_documento").addClass("is-invalid");
                camposValidos = false;
            }
            
            if (!$("#id_nombre_completo").val()) {
                $("#nombre-completo-error").text("El nombre completo es requerido").show();
                $("#id_nombre_completo").addClass("is-invalid");
                camposValidos = false;
            }
            
            if (!$("#id_telefono").val()) {
                $("#telefono-error").text("El teléfono es requerido").show();
                $("#id_telefono").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validación básica de correo
            const correo = $("#id_correo").val();
            if (correo && !correo.includes("@")) {
                $("#correo-error").text("Ingrese un correo electrónico válido").show();
                $("#id_correo").addClass("is-invalid");
                camposValidos = false;
            }
        }
        else if (paso === "venta") {
            // Validar campos de la pestaña de datos de venta
            
            // Validar tipo de cliente
            if (!$("#id_tipo_cliente").val()) {
                $("#tipo-cliente-error").text("El tipo de cliente es requerido").show();
                $("#id_tipo_cliente").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validar segmento
            if (!$("#id_segmento").val()) {
                $("#segmento-error").text("El segmento es requerido").show();
                $("#id_segmento").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validar plan adquirido
            if (!$("#id_plan_adquiere").val()) {
                $("#plan-error").text("El plan adquirido es requerido").show();
                $("#id_plan_adquiere").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validar número de contacto
            if (!$("#id_numero_contacto").val()) {
                $("#numero-contacto-error").text("El número de contacto es requerido").show();
                $("#id_numero_contacto").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validar NIP para portabilidades
            const segmento = $("#id_segmento").val();
            const tipoCliente = $("#id_tipo_cliente").val();
            if (segmento === "movil" && tipoCliente === "existente" && !$("#id_nip").val()) {
                $("#nip-error").text("El NIP es requerido para portabilidades").show();
                $("#id_nip").addClass("is-invalid");
                camposValidos = false;
            }
            
            // Validar IMEI para ventas de móviles nuevos
            if (segmento === "movil" && tipoCliente === "nuevo" && !$("#id_imei").val()) {
                $("#imei-error").text("El IMEI es requerido para clientes nuevos de móvil").show();
                $("#id_imei").addClass("is-invalid");
                camposValidos = false;
            }
        }
        else if (paso === "documento") {
            // Validación para documentos requeridos
            if (!$("#documento_identidad").val()) {
                $("#documento-identidad-error").show();
                $("#documento_identidad").addClass("is-invalid");
                camposValidos = false;
            }
            
            if (!$("#contrato_firmado").val()) {
                $("#contrato-firmado-error").show();
                $("#contrato_firmado").addClass("is-invalid");
                camposValidos = false;
            }
            
            if (!$("#confronta").val()) {
                $("#confronta-error").show();
                $("#confronta").addClass("is-invalid");
                camposValidos = false;
            }
        }
        
        return camposValidos;
    }
});
