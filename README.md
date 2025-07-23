# CREA Online CRM

Sistema integral de gestión para campañas de cartera, ventas de Telefónica, tickets de soporte, chat interno y control de calidad.

## 🚀 Características principales

### Módulo Campaña de Cartera
- **Gestión de Clientes**
  - Base de datos de deudores
  - Seguimiento de estados de contacto
  - Registro de gestiones
- **Acuerdos de Pago**
  - Creación y seguimiento de acuerdos
  - Cálculo de descuentos
  - Registro de pagos
- **Seguimientos**
  - Notificaciones automáticas
  - Calendario de seguimientos

### Módulo Telefónica
- **Gestión de Ventas**
  - Portabilidad: Gestión completa del proceso de portabilidad
  - PrePos: Ventas a clientes prepago que pasan a pospago
  - Upgrade: Mejora de planes para clientes existentes
- **Bandejas de Trabajo**
  - Pendientes: Ventas en proceso de revisión
  - Digitación: Ventas que requieren ingreso de datos
  - Seguimiento: Control de estado de ventas
  - Devueltas: Ventas con observaciones a corregir
- **Gestión de Clientes**
  - Base de datos de clientes PrePos y Upgrade
  - Carga masiva de clientes
  - Búsqueda y filtrado avanzado
- **Agendamientos**
  - Calendario de seguimiento a clientes
  - Gestión de estados (agendado, venta, volver a llamar, etc.)
  - Vista de calendario mensual
- **Comisiones**
  - Cálculo automático de comisiones por ventas
  - Reportes por agente y período
- **Reportería Avanzada**
  - Exportación a Excel de todos los módulos
  - Filtros por fechas y campos personalizables
  - Selección automática de todos los campos disponibles
  - Reportes de ventas (Portabilidad, PrePos, Upgrade)
  - Reportes de agendamientos y comisiones
  - Reportes de escalamientos y planes

### Módulo Chat
- **Comunicación Interna**
  - Chat entre usuarios del sistema
  - Mensajes masivos de supervisores a asesores
  - Notificación de mensajes no leídos

### Módulo Tickets
- **Sistema de Soporte Interno**
  - Creación y seguimiento de tickets
  - Categorización por tipo y prioridad
  - Asignación a responsables
  - Seguimiento de tiempos de resolución
- **Múltiples Aplicativos**
  - Soporte para Cartera, Telefónica y Vicidial

### Módulo Calidad
- **Control de Calidad**
  - Evaluación de gestiones
  - Monitoreo de llamadas
  - Reportes de calidad

### Seguridad
- **Autenticación por Roles**
  - Agente, backoffice, supervisor, administrador
  - Control de acceso basado en permisos
  - Registro de actividades

## 🛠️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd crea_online_crm
   ```

2. **Configurar entorno virtual**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   - Crea un archivo `.env` basado en `.env.example`
   - Configura las variables necesarias (base de datos, correo, etc.)

5. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar servidor**
   ```bash
   python manage.py runserver
   ```
   
   El sistema estará disponible en: http://127.0.0.1:8000/

## 🎨 Interfaz de Usuario

- Diseño responsivo con Bootstrap 5
- Menú lateral personalizado según rol del usuario
- Componentes modernos y accesibles
- Notificaciones en tiempo real para seguimientos y mensajes

## 📊 Módulos Principales

### Módulo Core
- Gestión de usuarios y perfiles
- Dashboard con estadísticas
- Seguimientos y notificaciones
- Gestión de cartera y acuerdos de pago
- Empleados y supervisores

### Módulo Telefónica
- Gestión de ventas (Portabilidad, PrePos, Upgrade)
- Administración de planes
- Bandejas de trabajo
- Agendamientos y calendario
- Comisiones
- **Sistema de Reportes**
  - Exportación masiva a Excel
  - Filtros avanzados por fecha y tipo
  - Campos personalizables para exportación
  - Reportes consolidados de todas las operaciones

### Módulo Chat
- Comunicación interna entre usuarios
- Mensajes directos y masivos
- Notificaciones de nuevos mensajes

### Módulo Tickets
- Sistema de soporte interno
- Seguimiento de incidencias y requerimientos
- Priorización y asignación de tickets

### Módulo Calidad
- Evaluación de gestiones
- Monitoreo de calidad
- Reportes de desempeño

## 📋 Requisitos del Sistema

- Python 3.8+
- Django 4.2+
- Base de datos PostgreSQL (recomendado) o SQLite
- Navegador web moderno

## 📂 Manejo de archivos media en producción (Railway)

- **Ruta persistente:** En Railway, los archivos subidos (confrontas, documentos, etc.) se almacenan en la ruta `/app/media`, que es persistente entre despliegues.
- **Configuración en Django:**
  ```python
  MEDIA_URL = '/media/'
  MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
  ```
- **Creación automática:** El sistema crea la carpeta de medios al iniciar si no existe.
- **Importante:**
  - Asegúrate de que tus rutas de guardado y lectura de archivos usen siempre `settings.MEDIA_ROOT`.
  - Si necesitas acceso persistente a los archivos tras reinicios/despliegues, usa siempre la ruta configurada en las variables de entorno.

## 🔄 Sesiones y Autenticación

- Duración de sesión: 12 horas (configurable)
- Redirección automática al login cuando la sesión expira
- Control de acceso basado en grupos de usuarios

## 📝 Licencia

Este proyecto es de uso interno de SINERGY. Todos los derechos reservados.

---

💡 **Nota:** Para soporte técnico, contactar al equipo de desarrollo jhonmoreno151@gmail.com whatsapp +573108647211.
