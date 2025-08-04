# Módulo Tarjeta Plata - CRM

## Descripción
Módulo especializado para la gestión de ventas de tarjetas de crédito "Plata" dirigidas al mercado mexicano. Forma parte del sistema integral CREA Online CRM.

## Funcionalidades Principales

### 1. Gestión de Clientes
- **Base de datos de clientes potenciales** con información completa
- **Evaluación de factibilidad** (Factible, No Factible, Pendiente)
- **Clasificación por tipo** (Prospecto, Cliente, Lead)
- **Carga masiva** de clientes mediante archivos Excel
- **Exportación** de datos a Excel

### 2. Gestión de Ventas
- **Formulario de captura** de ventas con validaciones en tiempo real
- **Estados de venta**: Nueva, Aceptada, Rechazada
- **Campo ID_PreAp** editable por el asesor (obtenido de la plataforma del banco)
- **Seguimiento completo** del ciclo de vida de la venta

### 3. Bandejas de Trabajo
- **Bandeja de Nuevas**: Ventas pendientes de validación
- **Bandeja de Aceptadas**: Ventas aprobadas y en proceso
- **Bandeja de Rechazadas**: Ventas rechazadas con motivos
- **Filtros avanzados** por fecha, agente, estado, etc.

### 4. Dashboard y Reportes
- **Dashboard interactivo** con métricas en tiempo real
- **Gráficos de ventas** por día, agente e históricos
- **Estadísticas consolidadas** y por estado
- **Exportación de reportes** a Excel

### 5. Sistema de Auditoría
- **Validación de ventas** por el backoffice
- **Auditoría de calidad** con call review y call upload
- **Historial de gestiones** y cambios de estado
- **Trazabilidad completa** de todas las acciones

## Modelos de Datos

### ClienteTarjetaPlata
- `item`: ID único del cliente
- `telefono`: Número de teléfono (único)
- `nombre_completo`: Nombre completo del cliente
- `factibilidad`: Estado de factibilidad
- `tipo`: Tipo de cliente
- `rfc`: RFC mexicano
- `fecha_nacimiento`: Fecha de nacimiento
- `genero`: Género del cliente
- `email`: Correo electrónico

### VentaTarjetaPlata
- `id_preap`: ID de preaprobación obtenido de la plataforma del banco (alfanumérico, hasta 50 caracteres)
- `item`: ID del registro
- `nombre`: Nombre del solicitante
- `ine`: Número de INE
- `rfc`: RFC del solicitante
- `telefono`: Teléfono de contacto
- `correo`: Correo electrónico
- `direccion`: Dirección completa
- `codigo_postal`: Código postal
- `estado_venta`: Estado actual de la venta
- `agente`: Usuario que registró la venta

### GestionBackofficeTarjetaPlata
- `item`: Relación con la venta
- `accion`: Tipo de acción realizada
- `motivo_rechazo`: Motivo en caso de rechazo
- `observaciones`: Observaciones adicionales
- `usuario`: Usuario que realizó la gestión

### AuditoriaBackofficeTarjetaPlata
- `id_auditoria_back`: ID único de auditoría
- `item`: Relación con la venta
- `call_review`: Estado de revisión de llamada
- `call_upload`: Estado de carga de llamada

## Roles y Permisos

### Asesores Tarjeta Plata
- Crear y editar clientes
- Registrar nuevas ventas
- Ver sus propias ventas
- Acceso al dashboard básico

### Backoffice Tarjeta Plata
- Todos los permisos de asesores
- Validar y rechazar ventas
- Gestionar bandejas de trabajo
- Realizar auditorías
- Acceso completo al dashboard

### Supervisores Tarjeta Plata
- Todos los permisos del sistema
- Gestión de usuarios y campañas
- Reportes avanzados
- Configuración del módulo

## Configuración Inicial

Para configurar el módulo por primera vez:

```bash
# Crear grupos de usuarios y permisos
python manage.py setup_tarjeta_plata --create-groups

# Crear campaña inicial
python manage.py setup_tarjeta_plata --create-campaign

# Crear datos de prueba (opcional)
python manage.py setup_tarjeta_plata --create-test-data

# Configuración completa
python manage.py setup_tarjeta_plata --create-groups --create-campaign --create-test-data
```

## URLs Principales

- `/tarjeta-plata/` - Dashboard principal
- `/tarjeta-plata/ventas/` - Lista de ventas
- `/tarjeta-plata/ventas/nueva/` - Crear nueva venta
- `/tarjeta-plata/bandeja/nuevas/` - Bandeja de ventas nuevas
- `/tarjeta-plata/bandeja/aceptadas/` - Bandeja de ventas aceptadas
- `/tarjeta-plata/bandeja/rechazadas/` - Bandeja de ventas rechazadas
- `/tarjeta-plata/clientes/` - Lista de clientes
- `/tarjeta-plata/clientes/nuevo/` - Crear nuevo cliente

## Tecnologías Utilizadas

- **Backend**: Django 4.x
- **Base de datos**: PostgreSQL
- **Frontend**: Bootstrap 5, Chart.js
- **Almacenamiento**: MinIO (para archivos)
- **Validaciones**: JavaScript en tiempo real
- **Exportación**: openpyxl para Excel

## Integración con el Sistema

El módulo se integra completamente con:
- **Sistema de usuarios** de Django
- **Modelo de campañas** del core
- **Sistema de permisos** granular
- **Middleware de auditoría** del sistema
- **Configuración de MinIO** para archivos

## Características Técnicas

### Validaciones
- RFC mexicano con formato correcto
- Códigos postales mexicanos válidos
- Teléfonos a 10 dígitos
- Validación de duplicados

### Seguridad
- Protección CSRF en todos los formularios
- Validación de permisos por vista
- Sanitización de datos de entrada
- Logs de auditoría completos

### Performance
- Consultas optimizadas con select_related
- Paginación en todas las listas
- Índices en campos de búsqueda
- Cache de estadísticas

## Mantenimiento

### Comandos Útiles
```bash
# Limpiar datos de prueba
python manage.py shell -c "from tarjeta_plata.models import *; VentaTarjetaPlata.objects.filter(agente__username='admin').delete()"

# Regenerar IDs únicos
python manage.py shell -c "from tarjeta_plata.models import *; [v.save() for v in VentaTarjetaPlata.objects.filter(id_preap='')]"

# Estadísticas del módulo
python manage.py shell -c "from tarjeta_plata.models import *; print(f'Clientes: {ClienteTarjetaPlata.objects.count()}, Ventas: {VentaTarjetaPlata.objects.count()}')"
```

### Monitoreo
- Revisar logs de Django para errores
- Monitorear uso de MinIO para archivos
- Verificar performance de consultas
- Auditar accesos y cambios

## Soporte

Para soporte técnico o reportar problemas:
1. Revisar los logs del sistema
2. Verificar configuración de base de datos
3. Comprobar permisos de usuarios
4. Consultar documentación de Django

---

**Versión**: 1.0.0  
**Última actualización**: Agosto 2025  
**Desarrollado para**: CREA Online CRM