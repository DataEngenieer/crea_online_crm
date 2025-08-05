# Módulo Tarjeta Plata 💳

Módulo especializado para la gestión de tarjetas de crédito Plata, incluyendo seguimiento de clientes, gestión de documentos, análisis de datos y procesamiento de imágenes con OCR.

## Características Principales

### 🎯 Gestión de Clientes
- **Registro de Clientes**: Sistema completo de información de clientes
- **Seguimiento de Estados**: Control de estados de solicitudes y gestiones
- **Gestión de Documentos**: Subida, validación y procesamiento OCR de documentos
- **Historial de Gestiones**: Seguimiento detallado de interacciones
- **Validación de Datos**: Verificación automática de información
- **Integración con MinIO**: Almacenamiento seguro de documentos en la nube

### 📊 Dashboard y Reportes
- **Dashboard Principal**: Métricas en tiempo real y KPIs
- **Estadísticas de Conversión**: Análisis de efectividad por asesor
- **Reportes de Gestión**: Seguimiento de actividades y productividad
- **Análisis de Tendencias**: Evolución de métricas clave
- **Exportación de Datos**: Comandos para exportar información
- **Gráficos Interactivos**: Visualización avanzada de datos

### 🔧 Configuración Avanzada
- **Estados Personalizables**: Configuración de flujos de trabajo
- **Permisos Granulares**: Control de acceso por roles y grupos
- **Integración con Core**: Sincronización con sistema principal
- **Validaciones Automáticas**: Verificación de datos y documentos
- **Procesamiento OCR**: Extracción automática de texto de imágenes
- **Restricción de IP**: Control de acceso por ubicación geográfica

## Modelos Principales

### ClienteTarjetaPlata
- `nombre`: Nombre completo del cliente
- `cedula`: Número de identificación
- `telefono`: Número de contacto
- `email`: Correo electrónico
- `estado_solicitud`: Estado actual de la solicitud
- `asesor_asignado`: Usuario responsable
- `fecha_creacion`: Timestamp de creación
- `fecha_actualizacion`: Última modificación
- `observaciones`: Notas adicionales
- `id_unico`: Identificador único generado automáticamente

### GestionTarjetaPlata
- `cliente`: Referencia al cliente
- `asesor`: Usuario que realiza la gestión
- `tipo_gestion`: Tipo de actividad realizada
- `descripcion`: Detalle de la gestión
- `estado_anterior`: Estado previo del cliente
- `estado_nuevo`: Nuevo estado asignado
- `fecha_gestion`: Timestamp de la gestión
- `observaciones`: Comentarios adicionales

### DocumentoTarjetaPlata
- `cliente`: Cliente asociado
- `tipo_documento`: Tipo de documento (cédula, ingresos, etc.)
- `archivo`: Archivo subido (local)
- `texto_extraido`: Texto extraído por OCR
- `minio_url`: URL del archivo en MinIO
- `minio_object_name`: Nombre del objeto en MinIO
- `subido_a_minio`: Estado de subida a MinIO
- `fecha_subida`: Timestamp de subida
- `procesado_ocr`: Estado del procesamiento OCR
- `usuario_subida`: Usuario que subió el archivo

### EstadoSolicitud
- `nombre`: Nombre del estado
- `descripcion`: Descripción del estado
- `activo`: Estado activo/inactivo
- `orden`: Orden de visualización
- `color`: Color para identificación visual

### ConfiguracionModulo
- `clave`: Clave de configuración
- `valor`: Valor de la configuración
- `descripcion`: Descripción de la configuración
- `activo`: Estado activo/inactivo

## Permisos y Seguridad

### Grupos de Usuario
- **"Asesores Tarjeta Plata"**: Acceso completo al módulo
- **"Administrador"**: Acceso total al sistema y configuración
- **"Supervisores"**: Acceso de supervisión y reportes

### Restricciones de IP
- **Middleware global**: Sistema de restricción de IP a nivel de aplicación
- **Configuración por entorno**: Activación automática en producción
- **Análisis de riesgo**: Integración con ipquery.io para detectar VPN/Proxy
- **Registro de accesos**: Log detallado de todos los intentos de acceso
- **Gestión de IPs**: Panel web y comandos CLI para administración

### Comandos de Gestión de Seguridad
```bash
# Listar IPs permitidas
python manage.py manage_ips list

# Agregar IP permitida
python manage.py manage_ips add 192.168.1.100 "Oficina Tarjeta Plata"

# Ver estadísticas de acceso
python manage.py manage_ips stats

# Consultar información de IP
python manage.py manage_ips info 186.86.110.237
```

### Validaciones y Auditoría
- **Control de acceso por campaña**: Validación automática de asignación
- **Validación de permisos por vista**: Decoradores de seguridad
- **Auditoría de acciones**: Registro de todas las operaciones
- **Validación de documentos**: Verificación de formato y contenido
- **Trazabilidad completa**: Seguimiento de cambios y modificaciones

## Instalación y Configuración

### 1. Migraciones
```bash
python manage.py migrate
```

### 2. Crear Grupos y Permisos
```bash
# Crear grupo "Asesores Tarjeta Plata"
python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Asesores Tarjeta Plata')"

# Crear grupo "Administrador" si no existe
python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Administrador')"
```

### 3. Crear Campaña de Tarjeta Plata
```bash
# Crear campaña para el módulo
python manage.py shell -c "from core.models import Campana; Campana.objects.get_or_create(nombre='Tarjeta Plata', modulo='Tarjeta Plata')"
```

### 4. Asignar Usuarios a Grupos
```bash
# Asignar usuario al grupo Asesores Tarjeta Plata
python manage.py shell -c "from django.contrib.auth.models import User, Group; user = User.objects.get(username='nombre_usuario'); group = Group.objects.get(name='Asesores Tarjeta Plata'); user.groups.add(group)"
```

### 5. Configurar Variables de Entorno
```env
# Configuración de MinIO (requerido para producción)
MINIO_ENDPOINT=https://tu-minio-endpoint.com
MINIO_ACCESS_KEY=tu_access_key
MINIO_SECRET_KEY=tu_secret_key

# Sistema de restricción de IPs (opcional)
IP_RESTRICTION_ENABLED=True

# Configuración de OCR (opcional)
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe  # Windows
# TESSERACT_CMD=/usr/bin/tesseract  # Linux
```

### 6. Configuración de Estados
1. Acceder al módulo de Tarjeta Plata
2. Ir a **Configuración** → **Estados**
3. Configurar estados de solicitudes
4. Definir flujos de trabajo

## Uso del Sistema

### Acceso al Módulo
1. Iniciar sesión con usuario del grupo "Asesores Tarjeta Plata"
2. Navegar a `/tarjeta_plata/` en el sistema
3. Acceder al dashboard principal

### Gestión de Clientes
1. Hacer clic en "Nuevo Cliente"
2. Completar información básica del cliente
3. Subir documentos requeridos (cédula, ingresos, etc.)
   - En producción: Se suben automáticamente a MinIO
   - En desarrollo: Se almacenan localmente
   - OCR automático: Extracción de texto de imágenes
4. Asignar estado inicial de la solicitud
5. Guardar registro

### Seguimiento de Gestiones
1. Seleccionar cliente existente
2. Ir a **Gestiones** → **Nueva Gestión**
3. Registrar actividad realizada
4. Actualizar estado si es necesario
5. Adjuntar documentos adicionales si se requiere
6. Guardar gestión con timestamp automático

### Procesamiento de Documentos
1. Subir imagen de documento (JPG, PNG, PDF)
2. El sistema procesará automáticamente:
   - Conversión de PDF a imágenes
   - Extracción de texto con OCR (Tesseract)
   - Almacenamiento en MinIO (producción)
   - Validación de formato y calidad
3. Revisar texto extraído y corregir si es necesario
4. Asociar documento al cliente correspondiente

## Estructura del Módulo

```
tarjeta_plata/
├── models.py              # Modelos de datos
├── views.py               # Vistas y lógica de negocio
├── forms.py               # Formularios
├── urls.py                # Configuración de URLs
├── admin.py               # Configuración del admin
├── utils.py               # Utilidades y funciones auxiliares
├── ocr_utils.py           # Funciones de procesamiento OCR
├── templates/             # Plantillas HTML
│   └── tarjeta_plata/
├── static/                # Archivos estáticos
│   └── tarjeta_plata/
├── migrations/            # Migraciones de base de datos
├── management/            # Comandos de gestión
│   └── commands/
│       ├── limpiar_datos_prueba.py
│       ├── regenerar_ids_unicos.py
│       └── estadisticas_modulo.py
└── README.md              # Documentación del módulo
```

## Integración con Otros Módulos

### Core
- **Modelos base**: Usuario, Campaña, Gestion
- **Sistema de permisos**: Integración con grupos y decoradores
- **Utilidades comunes**: Funciones compartidas y middleware
- **Configuración global**: Variables de entorno y settings

### MinIO
- **Almacenamiento de documentos**: Subida automática en producción
- **Gestión de buckets**: Bucket específico para tarjeta_plata
- **URLs seguras**: Generación de URLs temporales para acceso
- **Migración de archivos**: Comandos para migrar archivos locales

### Sistema de Restricción de IP
- **Middleware global**: Validación automática de acceso
- **Configuración centralizada**: Gestión desde el módulo core
- **Logs unificados**: Registro centralizado de accesos

### OCR y Procesamiento
- **Tesseract OCR**: Extracción de texto de imágenes
- **PDF2Image**: Conversión de PDFs a imágenes
- **Pillow**: Procesamiento de imágenes
- **Validación automática**: Verificación de calidad de documentos

## Troubleshooting

### Problemas Comunes

1. **Error de permisos**
   - Verificar que el usuario esté en el grupo "Asesores Tarjeta Plata"
   - Verificar asignación a la campaña "Tarjeta Plata"
   - Verificar configuración de restricción de IP

2. **Error de subida de archivos**
   - Verificar configuración de MinIO en producción
   - Verificar configuración de MEDIA_ROOT en desarrollo
   - Verificar permisos de escritura en directorios
   - Revisar logs de subida en la consola

3. **Error de procesamiento OCR**
   - Verificar instalación de Tesseract OCR
   - Verificar configuración de TESSERACT_CMD
   - Verificar formato de imagen soportado
   - Revisar calidad de la imagen

4. **Problemas con MinIO**
   - Verificar configuración de variables de entorno
   - Verificar conectividad con el endpoint de MinIO
   - Revisar permisos de buckets
   - Usar comandos de migración para solucionar archivos

5. **Error de acceso a módulo**
   - Verificar que las URLs estén incluidas
   - Verificar que la app esté en INSTALLED_APPS
   - Verificar IP permitida si está en producción

### Comandos de Diagnóstico
```bash
# Verificar estado de archivos en MinIO
python manage.py shell -c "from tarjeta_plata.models import DocumentoTarjetaPlata; print(f'Total: {DocumentoTarjetaPlata.objects.count()}, En MinIO: {DocumentoTarjetaPlata.objects.filter(subido_a_minio=True).count()}')"

# Verificar configuración de MinIO
python manage.py shell -c "from django.conf import settings; print(f'Endpoint: {settings.MINIO_ENDPOINT}, Bucket: {settings.MINIO_BUCKET_TARJETA_PLATA}')"

# Verificar instalación de Tesseract
python manage.py shell -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### Logs y Debugging
- **Logs de Django**: Configuración estándar en `settings.LOGGING`
- **Logs de MinIO**: Información detallada en consola durante subida
- **Logs de OCR**: Información de procesamiento de documentos
- **Logs de IP**: Registro de accesos y restricciones

## Comandos de Gestión

### Limpieza de Datos
```bash
# Limpiar datos de prueba
python manage.py limpiar_datos_prueba

# Limpiar con confirmación
python manage.py limpiar_datos_prueba --confirmar

# Limpiar datos específicos
python manage.py limpiar_datos_prueba --tipo clientes
```

### Regeneración de IDs
```bash
# Regenerar IDs únicos para todos los clientes
python manage.py regenerar_ids_unicos

# Regenerar solo para clientes sin ID único
python manage.py regenerar_ids_unicos --solo-vacios

# Regenerar con formato específico
python manage.py regenerar_ids_unicos --formato "TP-{:06d}"
```

### Estadísticas del Módulo
```bash
# Ver estadísticas generales
python manage.py estadisticas_modulo

# Estadísticas detalladas
python manage.py estadisticas_modulo --detallado

# Estadísticas por período
python manage.py estadisticas_modulo --desde 2024-01-01 --hasta 2024-12-31
```

### Migración de Archivos
```bash
# Migrar documentos locales a MinIO
python manage.py shell -c "from tarjeta_plata.utils import migrar_documentos_minio; migrar_documentos_minio()"

# Limpiar archivos locales ya subidos
python manage.py shell -c "from tarjeta_plata.utils import limpiar_archivos_locales; limpiar_archivos_locales()"
```

## Comandos Útiles de Django Shell

```python
# Limpiar datos de prueba
from tarjeta_plata.models import *
ClienteTarjetaPlata.objects.filter(nombre__icontains='test').delete()
GestionTarjetaPlata.objects.filter(descripcion__icontains='prueba').delete()

# Regenerar IDs únicos
for cliente in ClienteTarjetaPlata.objects.filter(id_unico__isnull=True):
    cliente.save()  # Trigger auto-generation

# Estadísticas del módulo
print(f"Clientes: {ClienteTarjetaPlata.objects.count()}")
print(f"Gestiones: {GestionTarjetaPlata.objects.count()}")
print(f"Documentos: {DocumentoTarjetaPlata.objects.count()}")
print(f"Documentos en MinIO: {DocumentoTarjetaPlata.objects.filter(subido_a_minio=True).count()}")
```

## Contribución

Para contribuir al módulo:
1. Seguir las convenciones de código del proyecto
2. Documentar nuevas funcionalidades
3. Mantener compatibilidad con el sistema principal
4. Probar exhaustivamente antes de implementar
5. Validar funcionamiento con MinIO y OCR
6. Considerar impacto en rendimiento

## Soporte

Para soporte técnico:
- **Email**: jhonmoreno151@gmail.com
- **WhatsApp**: +573108647211
- **Sistema de tickets**: Crear ticket en el CRM
- **Documentación**: Revisar README y logs del sistema