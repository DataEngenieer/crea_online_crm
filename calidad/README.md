# Módulo de Calidad

## Descripción
El módulo de Calidad es una aplicación integral para la gestión y evaluación de la calidad en llamadas y atención al cliente. Incluye funcionalidades avanzadas de análisis de audio, transcripción automática y evaluación mediante inteligencia artificial.

## Características Principales

### 🎯 Gestión de Auditorías
- **Auditorías de calidad**: Evaluación sistemática de llamadas y gestiones
- **Matrices de evaluación**: Configuración de indicadores personalizables
- **Puntuación automática**: Cálculo de puntajes basado en criterios
- **Seguimiento de agentes**: Control de rendimiento individual
- **Tipos de monitoreo**: Speech Analytics, Al Lado, Grabación
- **Respuestas de auditoría**: Sistema de seguimiento de hallazgos

### 🎙️ Análisis de Audio con IA
- **Transcripción automática**: Conversión de audio a texto usando Whisper (Replicate)
- **Análisis de sentimientos**: Evaluación del tono usando DeepSeek
- **Métricas de audio**: Duración, calidad, tamaño y características técnicas
- **Procesamiento en background**: Análisis asíncrono para mejor rendimiento
- **Almacenamiento en MinIO**: Gestión de archivos en la nube
- **Migración automática**: Comandos para migrar archivos locales a MinIO

### 📊 Reportes y Dashboards
- **Dashboard principal**: Métricas en tiempo real
- **Estadísticas de uso**: Consumo de servicios de IA (tokens, costos)
- **Reportes de auditoría**: Análisis detallado de resultados
- **Tendencias de calidad**: Evolución temporal de métricas
- **Exportación de datos**: Comando para exportar matrices de calidad

### 🔧 Configuración Avanzada
- **Matrices personalizables**: Adaptación a diferentes tipologías
- **Permisos granulares**: Control de acceso por roles y grupos
- **Integración con IA**: Conexión con Replicate y DeepSeek
- **Gestión de costos**: Control y monitoreo de uso de APIs externas
- **Restricción de IP**: Control de acceso por ubicación geográfica

## Instalación y Configuración

### 1. Migraciones
```bash
python manage.py migrate
```

### 2. Crear Grupos y Permisos
```bash
# Crear grupo "Calidad"
python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Calidad')"

# Crear grupo "Administrador" si no existe
python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Administrador')"
```

### 3. Crear Campaña de Calidad
```bash
# Crear campaña para el módulo
python manage.py shell -c "from core.models import Campana; Campana.objects.get_or_create(nombre='Calidad', modulo='Calidad')"
```

### 4. Asignar Usuarios a Grupos
```bash
# Asignar usuario al grupo Calidad
python manage.py shell -c "from django.contrib.auth.models import User, Group; user = User.objects.get(username='nombre_usuario'); group = Group.objects.get(name='Calidad'); user.groups.add(group)"
```

### 5. Configurar Variables de Entorno
```env
# Configuración de MinIO (requerido para producción)
MINIO_ENDPOINT=https://tu-minio-endpoint.com
MINIO_ACCESS_KEY=tu_access_key
MINIO_SECRET_KEY=tu_secret_key

# APIs de IA (opcional, para transcripción y análisis)
REPLICATE_API_TOKEN=tu_token_replicate
DEEPSEEK_API_KEY=tu_key_deepseek

# Sistema de restricción de IPs (opcional)
IP_RESTRICTION_ENABLED=True
```

### 6. Configurar Matriz de Calidad
- Acceder al panel de administración
- Crear indicadores en "Matriz Calidad"
- Configurar tipologías: Atención Telefónica, Ofrecimiento Comercial, Proceso de Venta
- Definir criterios de evaluación y ponderaciones

## Uso del Sistema

### Acceso al Módulo
1. Iniciar sesión con usuario del grupo "Calidad"
2. Navegar a `/calidad/` en el sistema
3. Acceder al dashboard principal

### Crear Auditoría
1. Hacer clic en "Nueva Auditoría"
2. Seleccionar agente y fecha de llamada
3. Elegir tipo de monitoreo (Speech Analytics, Al Lado, Grabación)
4. Subir archivo de audio (opcional)
   - En producción: Se sube automáticamente a MinIO
   - En desarrollo: Se almacena localmente
5. Completar evaluación de indicadores
6. Guardar auditoría

### Análisis de Audio
1. Subir archivo de audio en formato compatible (MP3, WAV, OGG, M4A, MPEG)
2. El sistema procesará automáticamente en background:
   - Transcripción del audio usando Whisper
   - Análisis de sentimientos con DeepSeek
   - Métricas técnicas (duración, tamaño, tokens)
   - Almacenamiento en MinIO (producción)
3. Revisar resultados en la auditoría
4. Seguimiento de costos de procesamiento

### Gestión de Archivos
```bash
# Migrar archivos locales a MinIO
python manage.py migrar_audios_minio

# Migración con simulación (dry-run)
python manage.py migrar_audios_minio --dry-run

# Forzar migración de archivos ya marcados como subidos
python manage.py migrar_audios_minio --force

# Migrar archivo específico
python manage.py migrar_audios_minio --speech-id 123

# Limpiar archivos locales ya subidos a MinIO
python manage.py limpiar_archivos_locales
```

### Exportación de Datos
```bash
# Exportar matriz de calidad en formato personalizado
python manage.py export_matriz_calidad --output matriz_calidad.json --format custom

# Exportar en formato nativo de Django
python manage.py export_matriz_calidad --output matriz_django.json --format django
```

## Estructura del Módulo

```
calidad/
├── models.py              # Modelos de datos
├── views.py               # Vistas principales
├── views_audio.py         # Vistas para manejo de audio
├── forms.py               # Formularios
├── forms_auditoria.py     # Formularios de auditoría
├── forms_speech.py        # Formularios de speech
├── urls.py                # Configuración de URLs
├── api.py                 # APIs del módulo
├── decorators.py          # Decoradores de seguridad
├── permissions.py         # Permisos personalizados
├── middleware.py          # Middleware específico
├── utils/                 # Utilidades
│   ├── analisis_de_calidad.py
│   ├── audio_utils.py
│   ├── graficar_audio.py
│   ├── texto_de_speech.py
│   └── whixperx.py
├── templates/calidad/     # Templates HTML
├── static/calidad/        # Archivos estáticos
└── management/commands/   # Comandos de gestión
```

## Modelos Principales

### Auditoria
- `agente`: Usuario evaluado
- `fecha_llamada`: Fecha de la llamada auditada
- `tipo_monitoreo`: Tipo de monitoreo (speech, al_lado, grabacion)
- `evaluador`: Usuario que realiza la auditoría
- `fecha_creacion`: Timestamp de creación
- `fecha_actualizacion`: Última modificación

### MatrizCalidad
- `indicador`: Descripción del criterio a evaluar
- `tipologia`: Tipo de interacción (atencion_telefonica, ofrecimiento_comercial, proceso_venta)
- `peso`: Ponderación del indicador (1-100)
- `activo`: Estado del indicador
- `usuario_creacion`: Usuario que creó el indicador
- `fecha_creacion`: Timestamp de creación

### DetalleAuditoria
- `auditoria`: Referencia a la auditoría
- `indicador`: Indicador evaluado
- `cumple`: Si cumple o no el criterio
- `observaciones`: Comentarios específicos
- `fecha_creacion`: Timestamp de creación

### Speech
- `auditoria`: Auditoría asociada
- `audio`: Archivo de audio (local)
- `transcripcion`: Texto transcrito por IA
- `analisis_ia`: Análisis de IA del audio
- `duracion_segundos`: Duración del audio
- `tamano_archivo_mb`: Tamaño del archivo
- `tokens_procesados`: Tokens consumidos en el análisis
- `tiempo_procesamiento`: Tiempo total de procesamiento
- `minio_url`: URL del archivo en MinIO
- `minio_object_name`: Nombre del objeto en MinIO
- `subido_a_minio`: Estado de subida a MinIO

### UsoProcesamientoAudio
- `speech`: Referencia al audio procesado
- `proveedor_transcripcion`: Servicio usado (Replicate, DeepSeek)
- `proveedor_analisis`: Servicio de análisis usado
- `tokens_transcripcion`: Tokens usados en transcripción
- `tokens_analisis`: Tokens usados en análisis
- `costo_transcripcion`: Costo de transcripción
- `costo_analisis`: Costo de análisis
- `costo_total`: Costo total del procesamiento
- `fecha_transcripcion`: Timestamp del procesamiento

### RespuestaAuditoria
- `auditoria`: Auditoría asociada
- `usuario_respuesta`: Usuario que responde
- `respuesta`: Contenido de la respuesta
- `fecha_respuesta`: Timestamp de la respuesta

## Permisos y Seguridad

### Grupos de Usuario
- **"Calidad"**: Acceso completo al módulo de calidad
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
python manage.py manage_ips add 192.168.1.100 "Oficina Calidad"

# Ver estadísticas de acceso
python manage.py manage_ips stats

# Consultar información de IP
python manage.py manage_ips info 186.86.110.237
```

### Decoradores de Seguridad
- `@grupo_requerido('Calidad')`: Requiere pertenecer al grupo
- `@ip_permitida`: Valida IP de acceso (deprecado - usar middleware global)
- **Middleware automático**: Validación automática en todas las vistas

## Integración con IA

### Transcripción de Audio
- **Proveedor**: Replicate (Whisper)
- **Formatos soportados**: MP3, WAV, OGG, M4A, MPEG
- **Procesamiento**: Asíncrono en background
- **Métricas**: Duración, tokens procesados, tiempo de procesamiento
- **Costo**: Calculado automáticamente por tokens
- **Almacenamiento**: MinIO en producción, local en desarrollo

### Análisis de Calidad
- **Proveedor**: DeepSeek
- **Funcionalidad**: Análisis automático de transcripciones
- **Métricas**: Puntajes de calidad, recomendaciones, análisis de sentimientos
- **Integración**: Procesamiento en tiempo real tras transcripción
- **Costos**: Control y monitoreo de uso de tokens

### Configuración de APIs
```env
# Variables de entorno requeridas
REPLICATE_API_TOKEN=r8_tu_token_aqui
DEEPSEEK_API_KEY=sk-tu_key_aqui
```

### Monitoreo de Costos
- **Tracking de tokens**: Registro detallado de consumo
- **Costos por proveedor**: Separación de costos de transcripción y análisis
- **Reportes de uso**: Dashboard con métricas de consumo
- **Alertas de presupuesto**: Configuración de límites de gasto

## Troubleshooting

### Problemas Comunes

1. **Error de permisos**
   - Verificar que el usuario esté en el grupo "Calidad"
   - Verificar asignación a la campaña "Calidad"
   - Verificar configuración de restricción de IP

2. **Error de transcripción**
   - Verificar formato de audio soportado
   - Verificar configuración de API keys (REPLICATE_API_TOKEN, DEEPSEEK_API_KEY)
   - Revisar logs de procesamiento en background
   - Verificar conectividad con servicios externos

3. **Error de acceso a módulo**
   - Verificar que las URLs estén incluidas
   - Verificar que la app esté en INSTALLED_APPS
   - Verificar IP permitida si está en producción

4. **Problemas con MinIO**
   - Verificar configuración de variables de entorno
   - Verificar conectividad con el endpoint de MinIO
   - Revisar permisos de buckets
   - Usar comandos de migración para solucionar archivos

5. **Archivos no se suben**
   - Verificar configuración de MinIO en producción
   - Revisar logs de subida en la consola
   - Usar comando de migración manual

### Comandos de Diagnóstico
```bash
# Verificar estado de archivos en MinIO
python manage.py shell -c "from calidad.models import Speech; print(f'Total: {Speech.objects.count()}, En MinIO: {Speech.objects.filter(subido_a_minio=True).count()}')"

# Verificar configuración de MinIO
python manage.py shell -c "from django.conf import settings; print(f'Endpoint: {settings.MINIO_ENDPOINT}, Buckets: {settings.MINIO_BUCKET_NAME}')"

# Listar archivos pendientes de migración
python manage.py migrar_audios_minio --dry-run
```

### Logs y Debugging
- **Logs de Django**: Configuración estándar en `settings.LOGGING`
- **Logs de MinIO**: Información detallada en consola durante subida
- **Logs de IA**: Tracking de procesamiento y costos
- **Logs de IP**: Registro de accesos y restricciones

## Comandos de Gestión

### Migración de Archivos
```bash
# Migrar todos los archivos a MinIO
python manage.py migrar_audios_minio

# Simulación sin cambios reales
python manage.py migrar_audios_minio --dry-run

# Forzar migración de archivos ya marcados
python manage.py migrar_audios_minio --force

# Migrar archivo específico
python manage.py migrar_audios_minio --speech-id 123
```

### Limpieza de Archivos
```bash
# Limpiar archivos locales ya subidos a MinIO
python manage.py limpiar_archivos_locales

# Simulación de limpieza
python manage.py limpiar_archivos_locales --dry-run

# Limpiar archivo específico
python manage.py limpiar_archivos_locales --speech-id 123
```

### Exportación de Datos
```bash
# Exportar matriz de calidad
python manage.py export_matriz_calidad --output matriz.json --format custom

# Exportar en formato Django nativo
python manage.py export_matriz_calidad --format django
```

### Estadísticas
```bash
# Estadísticas del módulo
python manage.py shell -c "from calidad.models import *; print(f'Auditorías: {Auditoria.objects.count()}, Transcripciones: {Speech.objects.count()}, En MinIO: {Speech.objects.filter(subido_a_minio=True).count()}')"
```

## Contribución

Para contribuir al módulo:
1. Seguir las convenciones de código del proyecto
2. Documentar nuevas funcionalidades
3. Mantener compatibilidad con el sistema principal
4. Probar exhaustivamente antes de implementar
5. Considerar impacto en costos de IA
6. Validar funcionamiento con MinIO

## Soporte

Para soporte técnico:
- **Email**: jhonmoreno151@gmail.com
- **WhatsApp**: +573108647211
- **Sistema de tickets**: Crear ticket en el CRM
- **Documentación**: Revisar README y logs del sistema