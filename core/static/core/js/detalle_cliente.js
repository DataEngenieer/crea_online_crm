document.addEventListener('DOMContentLoaded', function() {
    // Código para depurar el envío del formulario
    const formularioGestion = document.getElementById('gestion-form');
    const botonGuardar = document.getElementById('btn-guardar-gestion');
    
    // Verificar si los elementos existen
    if (formularioGestion) {
        console.log('Formulario de gestión encontrado, configurando listeners');
        
        // Detectar clic en el botón de guardar
        if (botonGuardar) {
            console.log('Botón de guardar encontrado, añadiendo listener de clic');
            botonGuardar.addEventListener('click', function(event) {
                console.log('=== CLIC EN BOTÓN GUARDAR DETECTADO ===');
                console.log('Tipo de evento:', event.type);
                console.log('Target:', event.target);
                console.log('Propiedades del botón:', {
                    id: this.id,
                    name: this.name,
                    type: this.type,
                    disabled: this.disabled,
                    className: this.className
                });
                
                // Verificar si hay cuotas para enviar como AJAX
                const acuerdoSection = document.getElementById('acuerdo_pago_section_container');
                const cuotasJsonValue = document.getElementById('cuotas-json')?.value;
                
                if (acuerdoSection && acuerdoSection.style.display !== 'none' && cuotasJsonValue && cuotasJsonValue !== '[]') {
                    // Marcar el formulario para procesamiento AJAX
                    formularioGestion.setAttribute('data-ajax-submit', 'true');
                }
                
                // No prevenimos el evento para que continue y se ejecute el submit
                // Solo estamos registrando que se hizo clic
            });
        } else {
            console.error('CRÍTICO: Botón de guardar NO encontrado');
        }

        // Depurar envío del formulario
        formularioGestion.addEventListener('submit', function(event) {
            // Prevenir temporalmente el envío para poder ver los datos
            event.preventDefault();
            
            console.log('=== DEPURACIÓN: EVENTO SUBMIT DEL FORMULARIO ===');
            console.log('Tipo de evento:', event.type);
            console.log('¿Event.defaultPrevented?', event.defaultPrevented);
            console.log('Form action:', this.action || 'No tiene action específico');
            console.log('Form method:', this.method || 'No tiene method específico');
            console.log('Form enctype:', this.enctype);
            
            const formData = new FormData(this);
            
            // Verificar campos clave
            console.log('\n=== CAMPOS CLAVE DEL FORMULARIO ===');
            console.log('¿Existe campo cliente?', formData.has('cliente'), formData.get('cliente'));
            console.log('¿Existe campo guardar_gestion?', formData.has('guardar_gestion'), formData.get('guardar_gestion'));
            console.log('¿Existe canal_contacto?', formData.has('canal_contacto'), formData.get('canal_contacto'));
            console.log('¿Existe estado_contacto?', formData.has('estado_contacto'), formData.get('estado_contacto'));
            console.log('¿Existe tipo_gestion_n1?', formData.has('tipo_gestion_n1'), formData.get('tipo_gestion_n1'));
            console.log('¿Existe csrfmiddlewaretoken?', formData.has('csrfmiddlewaretoken'));
            
            // Mostrar campos y valores
            console.log('\n=== TODOS LOS CAMPOS DEL FORMULARIO ===');
            const formDataObj = {};
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
                formDataObj[key] = value;
            }
            
            // Validar campos requeridos manualmente
            let camposVacios = [];
            let camposConError = formularioGestion.querySelectorAll('.invalid-feedback');
            if (camposConError.length > 0) {
                console.log('\n=== ERRORES DE VALIDACIÓN HTML ===');
                camposConError.forEach(campoError => {
                    console.log('Error encontrado:', campoError.textContent.trim());
                });
            }
            
            // Verificar si es un acuerdo de pago con cuotas para enviar como AJAX
            const acuerdoSection = document.getElementById('acuerdo_pago_section_container');
            const cuotasJsonValue = document.getElementById('cuotas-json')?.value;
            
            if (acuerdoSection && acuerdoSection.style.display !== 'none' && 
                cuotasJsonValue && cuotasJsonValue !== '[]' && 
                this.getAttribute('data-ajax-submit') === 'true') {
                
                console.log('\n=== ENVIANDO FORMULARIO VIA AJAX PARA CAPTURAR ID DE ACUERDO ===');
                
                // Agregar encabezado para indicar que es una solicitud AJAX
                const headers = {
                    'X-Requested-With': 'XMLHttpRequest'
                };
                
                // Enviar formulario mediante fetch
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: headers
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Respuesta del servidor:', data);
                    
                    // Actualizar el campo acuerdo_id con el ID recibido
                    if (data.acuerdo_id) {
                        document.getElementById('acuerdo_id').value = data.acuerdo_id;
                        console.log('Acuerdo ID actualizado:', data.acuerdo_id);
                        
                        // Mostrar el botón de múltiples pagos
                        const multiplePagosContainer = document.getElementById('multiple-pagos-container');
                        if (multiplePagosContainer) {
                            multiplePagosContainer.style.display = 'block';
                        }
                    }
                    
                    // Mostrar mensaje de éxito
                    if (data.mensaje) {
                        // Crear elemento de alerta
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-success alert-dismissible fade show';
                        alertDiv.role = 'alert';
                        alertDiv.innerHTML = `
                            ${data.mensaje}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        `;
                        
                        // Insertar alerta al principio del contenido
                        const container = document.querySelector('.container-fluid');
                        if (container) {
                            container.insertBefore(alertDiv, container.firstChild);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error al guardar el acuerdo:', error);
                    alert('Error al guardar el acuerdo. Por favor, inténtelo de nuevo.');
                });
            } else {
                // Continuar con el envío normal
                console.log('\n=== ENVIANDO FORMULARIO EN 1 SEGUNDO ===');
                setTimeout(() => {
                    console.log('Enviando formulario al servidor...');
                    this.submit();
                }, 1000);
            }
        });
    } else {
        console.error('No se encontró el formulario de gestión en la página');
    }
    
    // Ocultar los contenedores de acuerdo de pago y seguimiento al cargar la página
    const camposAcuerdo = document.getElementById('campos-acuerdo');
    const camposSeguimiento = document.getElementById('campos-seguimiento');
    
    if (camposAcuerdo) camposAcuerdo.style.display = 'none';
    if (camposSeguimiento) camposSeguimiento.style.display = 'none';
    
    // Función para mostrar/ocultar opciones en selectores dependientes
    function actualizarOpcionesVisibles(selectorPadre, selectorHijo) {
        const valorSeleccionado = selectorPadre.value;
        // Ocultar todas las opciones excepto la primera
        Array.from(selectorHijo.options).forEach((option, index) => {
            if (index === 0) return;
            option.style.display = 'none';
        });
        // Mostrar solo las opciones correspondientes al valor seleccionado
        let opcionesVisibles = 0;
        Array.from(selectorHijo.options).forEach(option => {
            if (option.getAttribute('data-parent') === valorSeleccionado) {
                option.style.display = '';
                opcionesVisibles++;
            }
        });
        // Resetear el valor del selector hijo
        selectorHijo.value = '';
        // Habilitar si hay opciones, deshabilitar si no
        selectorHijo.disabled = (opcionesVisibles === 0);
    }
    // Al cargar la página, asegúrate de habilitar los selects si hay opciones
    // Referencias a los campos de formulario (MOVIDAS ARRIBA)
    const estadoContactoSelect = document.getElementById('{{ gestion_form.estado_contacto.id_for_label }}');
    const tipoGestionN1Select = document.getElementById('{{ gestion_form.tipo_gestion_n1.id_for_label }}');
    const canalContactoSelect = document.getElementById('{{ gestion_form.canal_contacto.id_for_label }}');
    // const tipoGestionN2Select = document.getElementById('{{ gestion_form.tipo_gestion_n2.id_for_label }}'); // Descomentar si se usa

    // Al cargar la página, y después de declarar las constantes:
    if (!tipoGestionN1Select) {
        console.error("CRITICAL-INIT: El elemento select 'tipoGestionN1Select' (ID: {{ gestion_form.tipo_gestion_n1.id_for_label }}) NO fue encontrado en el DOM al inicializar.");
    } else {
        console.log("INIT: Elemento 'tipoGestionN1Select' (ID: {{ gestion_form.tipo_gestion_n1.id_for_label }}) encontrado correctamente.");
        // Habilitar el select si hay opciones y fue encontrado
        if (tipoGestionN1Select.options.length > 1) {
            tipoGestionN1Select.disabled = false;
        }
    }
    // if (tipoGestionN2Select && typeof tipoGestionN2Select !== 'undefined' && tipoGestionN2Select.options.length > 1) { // Si se usa tipoGestionN2Select
    //     tipoGestionN2Select.disabled = false;
    // }

    // Referencias a los contenedores de sección principales
    const acuerdoPagoSectionContainer = document.getElementById('acuerdo_pago_section_container');
    const seguimientoSectionContainer = document.getElementById('seguimiento_section_container');
    const comprobantePagoContainer = document.getElementById('comprobante_pago_container');
    const fechaPagoEfectivoContainer = document.getElementById('fecha_pago_efectivo_container');
    const urlTiposGestion = "{% url 'core:ajax_get_opciones_nivel2' %}";

    console.log('Elementos del DOM inicializados:', {
        canalContactoSelect,
        estadoContactoSelect,
        tipoGestionN1Select,
        acuerdoPagoSectionContainer,
        seguimientoSectionContainer,
        comprobantePagoContainer,
        fechaPagoEfectivoContainer
    });

    if (!estadoContactoSelect) console.error('ERROR: estadoContactoSelect no encontrado');
    if (!tipoGestionN1Select) console.error('ERROR: tipoGestionN1Select no encontrado');
    
    // Referencias a los campos de acuerdo de pago (el checkbox fue eliminado)
    const fechaAcuerdoGroup = document.getElementById('{{ gestion_form.fecha_acuerdo.id_for_label }}').closest('.mb-3');
    const montoAcuerdoGroup = document.getElementById('{{ gestion_form.monto_acuerdo.id_for_label }}').closest('.mb-3');
    const observacionesAcuerdoGroup = document.getElementById('{{ gestion_form.observaciones_acuerdo.id_for_label }}').closest('.mb-3');
    
    // Referencias a los campos de seguimiento (el checkbox fue eliminado)
    const camposSeguimientoDiv = document.getElementById('campos-seguimiento');
    
    // Establecer teléfono como opción por defecto en canal de contacto
    if (canalContactoSelect) {
        if (!canalContactoSelect.value) {
            canalContactoSelect.value = 'whatsapp';
        }
    }
    
    // Evento para cambio en estado de contacto
    if (estadoContactoSelect) {
        console.log('estadoContactoSelect encontrado. Añadiendo event listener.');
        estadoContactoSelect.addEventListener('change', function() {
            console.log('Estado contacto cambiado. ID:', this.value);
            const estadoContactoId = this.value;
            console.log('Estado de contacto seleccionado:', estadoContactoId);
            
            if (!tipoGestionN1Select) {
                console.error('CRITICAL: tipoGestionN1Select NO encontrado al inicio del evento change de estadoContactoSelect.');
                // return; // Podríamos detener la ejecución aquí si es crítico
            } else {
                console.log('tipoGestionN1Select SÍ encontrado al inicio del evento change.');
            }
            // Limpiar y deshabilitar tipoGestionN1Select antes de la carga.');
            
            // Limpiar y deshabilitar el selector de tipo de gestión
            if (tipoGestionN1Select) {
                tipoGestionN1Select.innerHTML = '';
                tipoGestionN1Select.disabled = true;
                console.log('tipoGestionN1Select limpiado y deshabilitado.');
            } else {
                console.error('ERROR: tipoGestionN1Select no encontrado al intentar limpiar/deshabilitar.');
                return; // Salir si el select no existe
            }
            
            if (estadoContactoId) {
                console.log(`Realizando fetch a: ${urlTiposGestion}?estado_contacto_id=${estadoContactoId}`);
                fetch(`${urlTiposGestion}?estado_contacto_id=${estadoContactoId}`)
                    .then(response => {
                        console.log('Respuesta de fetch recibida:', response);
                        if (!response.ok) {
                            console.error('Error en la respuesta de fetch:', response.status, response.statusText);
                            return response.text().then(text => { throw new Error('Respuesta de servidor no OK: ' + text); });
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Datos JSON recibidos para Tipo de Gestión:', data);
                        if (tipoGestionN1Select) {
                            updateSelectWithOptions(tipoGestionN1Select, data, 'Seleccione Tipo de Gestión');
                            tipoGestionN1Select.disabled = false;
                            console.log('Opciones de tipo de gestión cargadas y tipoGestionN1Select habilitado.');
                        } else {
                            console.error('ERROR: tipoGestionN1Select no encontrado al intentar actualizar opciones.');
                        }
                    })
                    .catch(error => {
                        console.error('Error en la petición AJAX para tipos de gestión o al procesar JSON:', error);
                        if (tipoGestionN1Select) {
                            tipoGestionN1Select.innerHTML = '<option value="">Error al cargar</option>'; // Mostrar error en el select
                            tipoGestionN1Select.disabled = false; // Habilitar para que el usuario vea el error
                        }
                    });
            } // Cierre del if (estadoContactoId)
        }); // Cierre del addEventListener
    } else {
        console.error('ERROR: estadoContactoSelect no encontrado, no se pudo añadir event listener.');
    }
    
    // Función para actualizar las opciones de un select (RESTAURADA)
    function updateSelectWithOptions(selectElement, options, defaultOptionText) {
        console.log('updateSelectWithOptions llamada con:', selectElement, options, defaultOptionText);
        if (!selectElement) {
            console.error('CRITICAL: selectElement es nulo en updateSelectWithOptions');
            return;
        }
        if (!Array.isArray(options)) {
            console.error('Error: las opciones no son un array.', options);
            // Mostrar un mensaje de error en el select
            selectElement.innerHTML = '<option value="">Error: Formato de opciones incorrecto</option>';
            return;
        }
        selectElement.innerHTML = ''; // Limpiar opciones existentes
        
        // Añadir opción por defecto
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultOptionText;
        selectElement.appendChild(defaultOption);

        // Añadir nuevas opciones
        options.forEach(function(option) {
            const opt = document.createElement('option');
            opt.value = option.value;
            opt.textContent = option.label;
            selectElement.appendChild(opt);
        });
    }
    
    // Evento para cambio en tipo de gestión
    tipoGestionN1Select.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const tipoGestionValue = this.value;
        console.log(`tipoGestionN1Select CHANGED. Value: '${tipoGestionValue}', Text: '${selectedOption ? selectedOption.text : 'N/A'}'`);
        toggleFieldsBasedOnSelection(tipoGestionValue);
    });
    
    // Si hay valores preseleccionados, disparar el evento change para cargar las opciones
    if (estadoContactoSelect && estadoContactoSelect.value) {
        console.log('Estado de contacto tiene valor preseleccionado:', estadoContactoSelect.value, '. Disparando evento change.');
        estadoContactoSelect.dispatchEvent(new Event('change'));
        // Si también hay un valor en tipo de gestión, aplicar la lógica condicional
        if (tipoGestionN1Select && tipoGestionN1Select.value) {
            console.log('Tipo de gestión tiene valor preseleccionado:', tipoGestionN1Select.value, '. Aplicando lógica condicional.');
            toggleFieldsBasedOnSelection(tipoGestionN1Select.value);
        }
    }
    
    // --- INICIO FUNCIONES DE GESTIÓN DE SECCIONES ---
    function manageAcuerdoPagoSection(show) {
        const section = document.getElementById('acuerdo_pago_section_container');
        const fieldsContainer = document.getElementById('campos-acuerdo');
        const fechaAcuerdoInput = document.getElementById('{{ gestion_form.fecha_acuerdo.id_for_label }}');
        const montoAcuerdoInput = document.getElementById('{{ gestion_form.monto_acuerdo.id_for_label }}');
        const observacionesAcuerdoInput = document.getElementById('{{ gestion_form.observaciones_acuerdo.id_for_label }}');

        if (section) section.style.display = show ? 'block' : 'none';
        if (fieldsContainer) fieldsContainer.style.display = show ? 'block' : 'none';

        const inputsToManage = [fechaAcuerdoInput, montoAcuerdoInput, observacionesAcuerdoInput];
        inputsToManage.forEach(input => {
            if (input) input.disabled = !show;
        });

        if (!show) {
            inputsToManage.forEach(input => {
                if (input) input.value = '';
            });
        }
    }

    function manageSeguimientoSection(show) {
        console.log(`manageSeguimientoSection llamada con show: ${show}`);
        const section = document.getElementById('seguimiento_section_container');
        const fieldsContainer = document.getElementById('campos-seguimiento');
        if (!section) console.error('manageSeguimientoSection: No se encontró seguimiento_section_container');
        if (!fieldsContainer) console.error('manageSeguimientoSection: No se encontró campos-seguimiento');
        const fechaSeguimientoInput = document.getElementById('{{ gestion_form.fecha_proximo_seguimiento.id_for_label }}');
        const horaSeguimientoInput = document.getElementById('{{ gestion_form.hora_proximo_seguimiento.id_for_label }}');
        const observacionesGeneralesInput = document.getElementById('{{ gestion_form.observaciones_generales.id_for_label }}');

        if (section) section.style.display = show ? 'block' : 'none';
        if (fieldsContainer) fieldsContainer.style.display = show ? 'block' : 'none';

        const inputsToManage = [fechaSeguimientoInput, horaSeguimientoInput, observacionesGeneralesInput];
        inputsToManage.forEach(input => {
            if (input) input.disabled = !show;
        });

        if (!show) {
            inputsToManage.forEach(input => {
                if (input) input.value = '';
            });
        }
    }

    // La función manageComprobantePagoSection ha sido eliminada ya que esta funcionalidad 
    // ahora se maneja con comprobante de pago en la pestaña de acuerdos
    // --- FIN FUNCIONES DE GESTIÓN DE SECCIONES ---
    
    // Función para validar campos interdependientes
    function validateForm() {
        let isValid = true;
        let messages = [];
        
        // Validar que se haya seleccionado un estado de contacto
        if (!estadoContactoSelect || !estadoContactoSelect.value) {
            isValid = false;
            messages.push('Debe seleccionar un estado de contacto.');
            if (estadoContactoSelect) estadoContactoSelect.classList.add('is-invalid');
        } else {
            if (estadoContactoSelect) estadoContactoSelect.classList.remove('is-invalid');
        }

        // Validar que se haya seleccionado un tipo de gestión N1
        if (!tipoGestionN1Select || !tipoGestionN1Select.value) {
            isValid = false;
            messages.push('Debe seleccionar un tipo de gestión.');
            if (tipoGestionN1Select) tipoGestionN1Select.classList.add('is-invalid');
        } else {
            if (tipoGestionN1Select) tipoGestionN1Select.classList.remove('is-invalid');
        }

        // Validar campos de Acuerdo de Pago si la sección está visible
        const acuerdoSection = document.getElementById('acuerdo_pago_section_container');
        if (acuerdoSection && acuerdoSection.style.display !== 'none') {
            const fechaAcuerdoInput = document.getElementById('{{ gestion_form.fecha_acuerdo.id_for_label }}');
            const montoAcuerdoInput = document.getElementById('{{ gestion_form.monto_acuerdo.id_for_label }}');
            const montoAcuerdoValidacion = document.getElementById('monto-acuerdo-validacion');
            
            if (!fechaAcuerdoInput.value) {
                isValid = false; messages.push('Acuerdo: Debe ingresar la fecha del acuerdo.'); fechaAcuerdoInput.classList.add('is-invalid');
            } else { fechaAcuerdoInput.classList.remove('is-invalid'); }
            
            if (!montoAcuerdoInput.value || parseFloat(montoAcuerdoInput.value) <= 0) {
                isValid = false; messages.push('Acuerdo: Debe ingresar un monto válido.'); montoAcuerdoInput.classList.add('is-invalid');
            } else { 
                montoAcuerdoInput.classList.remove('is-invalid'); 
                
                // Validar que la suma de las cuotas coincida con el monto del acuerdo (si hay cuotas)
                if (cuotas.length > 0) {
                    const montoTotal = parseFloat(montoAcuerdoInput.value);
                    const sumaCuotas = cuotas.reduce((sum, cuota) => sum + parseFloat(cuota.monto || 0), 0);
                    
                    if (Math.abs(montoTotal - sumaCuotas) > 0.01) { // Permitir una pequeña diferencia por redondeo
                        isValid = false;
                        messages.push('El monto total de las cuotas debe coincidir con el monto del acuerdo.');
                        if (montoAcuerdoValidacion) {
                            montoAcuerdoValidacion.style.display = 'block';
                            montoAcuerdoValidacion.textContent = `El monto del acuerdo ($${montoTotal.toFixed(2)}) debe coincidir con la suma de las cuotas ($${sumaCuotas.toFixed(2)})`;
                        }
                    } else if (montoAcuerdoValidacion) {
                        montoAcuerdoValidacion.style.display = 'none';
                    }
                }
            }
        }

        // Validar campos de Seguimiento si la sección está visible
        const seguimientoSection = document.getElementById('seguimiento_section_container');
        if (seguimientoSection && seguimientoSection.style.display !== 'none') {
            const fechaSeguimientoInput = document.getElementById('{{ gestion_form.fecha_proximo_seguimiento.id_for_label }}');
            const horaSeguimientoInput = document.getElementById('{{ gestion_form.hora_proximo_seguimiento.id_for_label }}');
            if (!fechaSeguimientoInput.value) {
                isValid = false; messages.push('Seguimiento: Debe ingresar la fecha.'); fechaSeguimientoInput.classList.add('is-invalid');
            } else { fechaSeguimientoInput.classList.remove('is-invalid'); }
            if (!horaSeguimientoInput.value) {
                isValid = false; messages.push('Seguimiento: Debe ingresar la hora.'); horaSeguimientoInput.classList.add('is-invalid');
            } else { horaSeguimientoInput.classList.remove('is-invalid'); }
        }

        // La validación de campos del comprobante de pago ha sido eliminada
        // ya que esta funcionalidad ahora se maneja con comprobante de pago en la pestaña de acuerdos

        if (!isValid) {
            alert('Por favor corrija los siguientes errores:\n- ' + messages.join('\n- '));
        }
        return isValid;
    }
    
    // Agregar validación al formulario
    const form = document.querySelector('#registrar-gestion form');
    form.addEventListener('submit', function(event) {
        if (!validateForm()) {
            event.preventDefault();
        }
    });
    
    // Configuración de los desplegables dependientes usando AJAX
    // La constante urlTiposGestion ya ha sido declarada y movida al inicio del DOMContentLoaded.
    // El addEventListener para estadoContactoSelect y la lógica de dispatchEvent ya están definidos anteriormente (around lines 800-900+)
    // por lo que este bloque if (estadoContactoSelect) { ... } que estaba aquí y contenía erróneamente
    // la declaración de fechaPagoEfectivoContainer y la definición de toggleFieldsBasedOnSelection
    // ya no es necesario en esta posición con ese contenido.
    // Si se necesita un if(estadoContactoSelect) para alguna lógica específica aquí, se debe añadir explícitamente.

    // Función para mostrar u ocultar secciones según la selección de tipo de gestión
    function toggleFieldsBasedOnSelection(tipoGestionValue) {
        console.log('toggleFieldsBasedOnSelection llamado con:', tipoGestionValue);
        // Ocultar todas las secciones primero
        manageAcuerdoPagoSection(false);
        manageSeguimientoSection(false);
        // Ya no se usa manageComprobantePagoSection porque esta funcionalidad
        // ahora se maneja con comprobante de pago en la pestaña de acuerdos

        if (!tipoGestionValue) return; // Si no hay valor, todas permanecen ocultas

        switch (tipoGestionValue) {
            case 'AP': // Acuerdo Pendiente
            case 'PP': // Promesa de Pago
                manageAcuerdoPagoSection(true);
                break;
            case 'SOLICITA_LLAMADA': // Solicita Llamada
                console.log("toggleFieldsBasedOnSelection: Entrando en caso 'SL' (Solicita Llamada)");
                manageSeguimientoSection(true);
                break;
            case 'NC': // Negociación en Curso
                console.log("toggleFieldsBasedOnSelection: Entrando en caso 'NC' (Negociación en Curso)");
                manageSeguimientoSection(true);
                break;
            // Añadir más casos según sea necesario
        }
    }
    
    // ===== INICIO: CÓDIGO PARA MÚLTIPLES FECHAS Y MONTOS DE PAGO =====
    // Referencias a elementos del DOM para múltiples pagos
    const btnAgregarCuota = document.getElementById('btn-agregar-cuota');
    const cuotasContainer = document.getElementById('cuotas-container');
    const cuotasJson = document.getElementById('cuotas-json');
    const totalCuotas = document.getElementById('total-cuotas');
    const totalMontos = document.getElementById('total-montos');
    const btnMultiplePagos = document.getElementById('btn-multiple-pagos');
    const multiplePagosContainer = document.getElementById('multiple-pagos-container');
    
    // Array para almacenar las cuotas
    let cuotas = [];
    
    // Función para actualizar el contador y el total de montos
    function actualizarResumen() {
        if (!totalCuotas || !totalMontos) return;
        
        totalCuotas.textContent = cuotas.length;
        
        const total = cuotas.reduce((sum, cuota) => sum + parseFloat(cuota.monto || 0), 0);
        totalMontos.textContent = total.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        
        // Actualizar el campo oculto con los datos de las cuotas en formato JSON
        if (cuotasJson) {
            cuotasJson.value = JSON.stringify(cuotas);
        }
        
        // Mostrar u ocultar el botón de múltiples pagos según si hay cuotas
        if (multiplePagosContainer) {
            const acuerdoId = document.getElementById('acuerdo_id')?.value;
            // Solo mostrar si hay cuotas Y hay un ID de acuerdo
            multiplePagosContainer.style.display = (cuotas.length > 0 && acuerdoId) ? 'block' : 'none';
        }
        
        // Validar si el monto total de las cuotas coincide con el monto del acuerdo
        const montoAcuerdoInput = document.getElementById('{{ gestion_form.monto_acuerdo.id_for_label }}');
        const montoAcuerdoValidacion = document.getElementById('monto-acuerdo-validacion');
        
        if (montoAcuerdoInput && montoAcuerdoInput.value && cuotas.length > 0) {
            const montoTotal = parseFloat(montoAcuerdoInput.value);
            
            if (Math.abs(montoTotal - total) > 0.01) { // Permitir una pequeña diferencia por redondeo
                if (montoAcuerdoValidacion) {
                    montoAcuerdoValidacion.style.display = 'block';
                    montoAcuerdoValidacion.textContent = `El monto del acuerdo ($${montoTotal.toFixed(2)}) debe coincidir con la suma de las cuotas ($${total.toFixed(2)})`;
                }
            } else if (montoAcuerdoValidacion) {
                montoAcuerdoValidacion.style.display = 'none';
            }
        }
    }
    
    // Función para agregar una nueva cuota
    function agregarCuota() {
        if (!cuotasContainer) return;
        
        const id = Date.now(); // ID único basado en timestamp
        const nuevaCuota = {
            id: id,
            fecha: '',
            monto: ''
        };
        
        cuotas.push(nuevaCuota);
        
        // Crear fila para la nueva cuota
        const tr = document.createElement('tr');
        tr.id = `cuota-${id}`;
        tr.innerHTML = `
            <td>
                <input type="date" class="form-control form-control-sm fecha-cuota" 
                       data-id="${id}" required>
            </td>
            <td>
                <div class="input-group input-group-sm">
                    <span class="input-group-text">$</span>
                    <input type="number" step="0.01" class="form-control form-control-sm monto-cuota" 
                           data-id="${id}" required>
                </div>
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-outline-danger eliminar-cuota" 
                        data-id="${id}">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        cuotasContainer.appendChild(tr);
        
        // Agregar event listeners a los nuevos campos
        const fechaInput = tr.querySelector('.fecha-cuota');
        const montoInput = tr.querySelector('.monto-cuota');
        const btnEliminar = tr.querySelector('.eliminar-cuota');
        
        fechaInput.addEventListener('change', function() {
            const id = this.getAttribute('data-id');
            const cuota = cuotas.find(c => c.id == id);
            if (cuota) {
                cuota.fecha = this.value;
                actualizarResumen();
            }
        });
        
        montoInput.addEventListener('change', function() {
            const id = this.getAttribute('data-id');
            const cuota = cuotas.find(c => c.id == id);
            if (cuota) {
                cuota.monto = this.value;
                actualizarResumen();
            }
        });
        
        btnEliminar.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            eliminarCuota(id);
        });
        
        actualizarResumen();
    }
    
    // Función para eliminar una cuota
    function eliminarCuota(id) {
        const index = cuotas.findIndex(c => c.id == id);
        if (index !== -1) {
            cuotas.splice(index, 1);
            const fila = document.getElementById(`cuota-${id}`);
            if (fila) fila.remove();
            actualizarResumen();
        }
    }
    
    // Event listener para el botón de agregar cuota
    if (btnAgregarCuota) {
        btnAgregarCuota.addEventListener('click', agregarCuota);
    }
    
    // Event listener para el botón de registrar múltiples pagos
    if (btnMultiplePagos) {
        btnMultiplePagos.addEventListener('click', function() {
            // Validar que todas las cuotas tengan fecha y monto
            const cuotasIncompletas = cuotas.filter(c => !c.fecha || !c.monto);
            if (cuotasIncompletas.length > 0) {
                alert('Todas las cuotas deben tener fecha y monto');
                return;
            }
            
            // Obtener el ID del acuerdo desde el formulario (si existe)
            const acuerdoId = document.querySelector('input[name="acuerdo_id"]')?.value;
            if (!acuerdoId) {
                alert('No se ha seleccionado un acuerdo de pago');
                return;
            }
            
            // Abrir la página de registro de múltiples pagos
            window.location.href = `{% url 'core:registrar_multiple_pagos' acuerdo_id=0 %}`.replace('0', acuerdoId);
        });
    }
    // ===== FIN: CÓDIGO PARA MÚLTIPLES FECHAS Y MONTOS DE PAGO =====
});