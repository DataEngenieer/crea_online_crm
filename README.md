# CREA Online CRM

Sistema integral de gestión para campañas de cartera, ventas de Telefónica, tickets de soporte, chat interno y control de calidad.

## 🚀 Características Principales

### 📊 Dashboard Interactivo
- Métricas en tiempo real de gestiones y tickets
- Gráficos dinámicos con Chart.js
- Filtros avanzados por fecha y estado
- Indicadores de rendimiento (KPIs)

### 🎫 Sistema de Tickets
- Creación y gestión de tickets de soporte
- Estados: Abierto, En Progreso, Resuelto, Cerrado
- Prioridades: Baja, Media, Alta, Crítica
- Asignación automática y manual
- Historial completo de cambios
- Sistema de comentarios
- Subida de archivos adjuntos

### 👥 Gestión de Clientes
- Base de datos completa de clientes
- Historial de gestiones por cliente
- Información de contacto y deudas
- Búsqueda avanzada y filtros
- Exportación de datos
- Sistema de acuerdos de pago y cuotas

### 📞 Módulo Telefónica
- Gestión de ventas prepago
- Seguimiento de agendamientos
- Dashboard específico con métricas
- Integración con el sistema principal
- Gestión de clientes PrePos y Upgrade

### 🎯 Módulo de Calidad
- Auditorías de calidad de llamadas
- Matrices de evaluación personalizables
- Análisis de audio con IA (Speech Analytics)
- Transcripción automática con Whisper
- Análisis de sentimientos con DeepSeek
- Integración con MinIO para almacenamiento
- Dashboard de métricas de calidad

### 💳 Módulo Tarjeta Plata
- Gestión de ventas de tarjetas de crédito
- Base de datos de clientes potenciales
- Sistema de backoffice y auditorías
- Validaciones específicas para México (RFC, CP)
- Bandejas de trabajo (Nuevos, Aceptados, Rechazados)
- Dashboard con métricas en tiempo real

### 🔒 Sistema de Restricción de IPs
- Control de acceso por IP en producción
- Integración con API ipquery.io
- Registro detallado de accesos
- Panel de gestión de IPs permitidas
- Comandos CLI para administración
- Análisis de riesgo y detección de VPN/Proxy

### 🔐 Sistema de Autenticación
- Login seguro con validación
- Control de acceso por grupos
- Sesiones persistentes
- Redirección inteligente
- Middleware de login requerido

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

### Módulo Chat
- **Comunicación Interna**
  - Chat entre usuarios del sistema
  - Mensajes masivos de supervisores a asesores
  - Notificación de mensajes no leídos

### Seguridad
- **Autenticación por Roles**
  - Agente, backoffice, supervisor, administrador
  - Control de acceso basado en permisos
  - Registro de actividades

## 🛠️ Tecnologías Utilizadas

- **Backend:** Django 5.2.1
- **Base de datos:** PostgreSQL (producción) / SQLite (desarrollo)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Formularios:** Django Crispy Forms con Bootstrap 5
- **Widgets:** Django Widget Tweaks
- **Gráficos:** Chart.js
- **Despliegue:** Railway
- **Almacenamiento:** MinIO (producción) / Sistema local (desarrollo)
- **IA y Transcripción:** Replicate (Whisper), DeepSeek
- **Procesamiento de Audio:** librosa, soundfile, ffmpeg-python
- **Análisis de Documentos:** pdf2image, pytesseract, Pillow
- **Exportación:** openpyxl para Excel
- **Autenticación:** Django Auth
- **APIs Externas:** ipquery.io para análisis de IPs
- **Utilidades:** requests, numpy, matplotlib

## 📦 Instalación

### Prerrequisitos
- Python 3.8+
- pip
- PostgreSQL (para producción)
- FFmpeg (para procesamiento de audio)
- Tesseract OCR (para análisis de documentos)

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd crea_online_crm
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crear archivo `.env` en la raíz del proyecto:
   ```env
   SECRET_KEY=tu_clave_secreta_aqui
   DEBUG=True
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/crea_crm
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Sistema de restricción de IPs (opcional)
   IP_RESTRICTION_ENABLED=False
   
   # Configuración de MinIO (producción)
   MINIO_ENDPOINT=https://tu-minio-endpoint.com
   MINIO_ACCESS_KEY=tu_access_key
   MINIO_SECRET_KEY=tu_secret_key
   
   # Configuración de email (opcional)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=tu_password
   ```

5. **Ejecutar migraciones:**
   ```bash
   python manage.py migrate
   ```

6. **Crear grupos y permisos:**
   ```bash
   # Crear grupos básicos
   python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Administrador'); Group.objects.get_or_create(name='Calidad'); Group.objects.get_or_create(name='Asesores Tarjeta Plata')"
   
   # Crear campañas
   python manage.py shell -c "from core.models import Campana; Campana.objects.get_or_create(nombre='Calidad', modulo='Calidad'); Campana.objects.get_or_create(nombre='Tarjeta Plata', modulo='Tarjeta Plata')"
   ```

7. **Crear superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Ejecutar servidor de desarrollo:**
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

## 📂 Manejo de archivos en producción

### MinIO (Recomendado para producción)
- **Almacenamiento en la nube:** Los archivos se almacenan en MinIO para persistencia total
- **Buckets configurados:**
  - `llamadas-crea-online`: Audios de calidad
  - `transcripciones-crea-online`: Transcripciones de audio
  - `tickets-crea-online`: Archivos de tickets
  - `telefonica-crea-online`: Archivos del módulo Telefónica
  - `tarjeta-plata-crea-online`: Archivos del módulo Tarjeta Plata
- **Migración automática:** Comando para migrar archivos locales a MinIO
- **Limpieza automática:** Comandos para limpiar archivos locales tras subida

### Railway (Fallback)
- **Ruta persistente:** En Railway, los archivos se almacenan en `/app/media`
- **Configuración en Django:**
  ```python
  MEDIA_URL = '/media/'
  MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
  ```
- **Creación automática:** El sistema crea las carpetas necesarias al iniciar

### Comandos de gestión de archivos
```bash
# Migrar archivos a MinIO
python manage.py migrar_audios_minio

# Limpiar archivos locales ya subidos
python manage.py limpiar_archivos_locales

# Migración con opciones
python manage.py migrar_audios_minio --dry-run
python manage.py migrar_audios_minio --force
```

## 🔄 Sesiones y Autenticación

- Duración de sesión: 12 horas (configurable)
- Redirección automática al login cuando la sesión expira
- Control de acceso basado en grupos de usuarios
- Middleware de login requerido para todas las vistas
- Sistema de restricción de IPs en producción
- Registro detallado de accesos y intentos de login

## 🛡️ Seguridad

### Restricción de IPs
- Control de acceso por IP en producción
- Análisis de riesgo con ipquery.io
- Detección de VPN, proxies y conexiones sospechosas
- Panel de gestión de IPs permitidas
- Comandos CLI para administración
- Logs detallados de todos los accesos

### Comandos de gestión de IPs
```bash
# Listar IPs permitidas
python manage.py manage_ips list

# Agregar IP permitida
python manage.py manage_ips add 192.168.1.100 "Oficina principal"

# Consultar información de IP
python manage.py manage_ips info 186.86.110.237

# Ver estadísticas de acceso
python manage.py manage_ips stats

# Limpiar registros antiguos
python manage.py manage_ips cleanup
```

## 🤖 Integración con IA

### Transcripción de Audio
- **Proveedor:** Replicate (Whisper)
- **Formatos soportados:** MP3, WAV, OGG, M4A, MPEG
- **Procesamiento:** Automático en background
- **Métricas:** Duración, tamaño, tokens procesados

### Análisis de Calidad
- **Proveedor:** DeepSeek
- **Funcionalidad:** Análisis automático de transcripciones
- **Métricas:** Puntajes de calidad y recomendaciones
- **Integración:** Procesamiento en tiempo real

## 📊 Comandos de Gestión

### Estadísticas del sistema
```bash
# Estadísticas generales
python manage.py shell -c "from core.models import *; print(f'Clientes: {Cliente.objects.count()}, Gestiones: {Gestion.objects.count()}')"

# Estadísticas de Tarjeta Plata
python manage.py shell -c "from tarjeta_plata.models import *; print(f'Clientes: {ClienteTarjetaPlata.objects.count()}, Ventas: {VentaTarjetaPlata.objects.count()}')"

# Estadísticas de Calidad
python manage.py shell -c "from calidad.models import *; print(f'Auditorías: {Auditoria.objects.count()}, Transcripciones: {Speech.objects.count()}')"
```

### Limpieza y mantenimiento
```bash
# Limpiar datos de prueba
python manage.py shell -c "from tarjeta_plata.models import *; VentaTarjetaPlata.objects.filter(agente__username='admin').delete()"

# Regenerar IDs únicos
python manage.py shell -c "from tarjeta_plata.models import *; [v.save() for v in VentaTarjetaPlata.objects.filter(id_preap='')]"

# Exportar matriz de calidad
python manage.py export_matriz_calidad --output matriz_calidad.json --format custom
```

## 📝 Licencia

Este proyecto es de uso interno de SINERGY. Todos los derechos reservados.

---

💡 **Nota:** Para soporte técnico, contactar al equipo de desarrollo jhonmoreno151@gmail.com whatsapp +573108647211.
