# Módulo de Calidad

## Descripción
El módulo de Calidad es una aplicación integral para la gestión y evaluación de la calidad en llamadas y atención al cliente. Incluye funcionalidades avanzadas de análisis de audio, transcripción automática y evaluación mediante inteligencia artificial.

## Características Principales

### 🎯 Gestión de Auditorías
- **Auditorías de Calidad**: Sistema completo para evaluar llamadas y interacciones
- **Matrices de Evaluación**: Configuración flexible de criterios de calidad
- **Puntajes Automáticos**: Cálculo automático de puntuaciones basado en criterios
- **Seguimiento de Agentes**: Evaluación individual y seguimiento de desempeño

### 🎙️ Análisis de Audio
- **Transcripción Automática**: Conversión de audio a texto usando IA
- **Análisis de Sentimientos**: Evaluación del tono y calidad de la conversación
- **Métricas de Audio**: Duración, tamaño de archivo y estadísticas de procesamiento
- **Visualización de Ondas**: Gráficos interactivos del audio

### 📊 Reportes y Dashboards
- **Dashboard Principal**: Vista general de métricas de calidad
- **Estadísticas de Uso**: Monitoreo del uso de recursos de transcripción
- **Reportes de Auditorías**: Análisis detallado de evaluaciones
- **Tendencias de Calidad**: Seguimiento de mejoras y áreas de oportunidad

### 🔧 Configuración Avanzada
- **Matrices Personalizables**: Creación de criterios específicos por tipología
- **Permisos Granulares**: Control de acceso por roles y funciones
- **Integración con IA**: Análisis automático usando modelos de lenguaje
- **Gestión de Costos**: Seguimiento de costos de transcripción y análisis

## Instalación y Configuración

### 1. Configuración Inicial
El módulo ya está integrado en el sistema. Para configurarlo:

```bash
# Ejecutar migraciones (ya realizado)
python manage.py migrate

# Configurar grupos y permisos (ya realizado)
python manage.py setup_calidad
```

### 2. Asignación de Usuarios
1. Acceder al admin de Django (`/admin/`)
2. Ir a **Grupos** y seleccionar **Calidad**
3. Asignar usuarios al grupo
4. Ir a **Campañas** y seleccionar **Calidad**
5. Asignar usuarios a la campaña

### 3. Configuración de Matrices
1. Acceder al módulo de Calidad
2. Ir a **Matriz de Calidad**
3. Crear indicadores y criterios de evaluación
4. Configurar ponderaciones y tipologías

## Uso del Sistema

### Acceso al Módulo
1. En la pantalla de login, seleccionar **Calidad**
2. Ingresar credenciales de usuario con permisos de calidad
3. Acceder al dashboard principal

### Crear una Auditoría
1. Ir a **Auditorías** → **Nueva Auditoría**
2. Completar información del agente y llamada
3. Subir archivo de audio (opcional)
4. Evaluar criterios de calidad
5. Guardar y generar puntaje

### Análisis de Audio
1. En una auditoría, subir archivo de audio
2. El sistema transcribirá automáticamente
3. Generar análisis de calidad con IA
4. Revisar resultados y ajustar evaluación

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

- **Auditoria**: Evaluaciones de calidad de llamadas
- **MatrizCalidad**: Criterios de evaluación
- **DetalleAuditoria**: Respuestas a criterios específicos
- **Speech**: Archivos de audio y transcripciones
- **UsoProcesamientoAudio**: Métricas de uso y costos

## Permisos y Seguridad

### Grupos de Usuario
- **Calidad**: Acceso completo al módulo
- **Administrador**: Acceso total al sistema

### Restricciones de IP
El módulo incluye middleware para restringir acceso por IP cuando sea necesario.

### Decoradores de Seguridad
- `@grupo_requerido('Calidad')`: Requiere pertenecer al grupo
- `@ip_permitida`: Valida IP de acceso

## Integración con IA

### Transcripción de Audio
- **Proveedor**: Replicate (Whisper)
- **Formatos soportados**: MP3, WAV, OGG, M4A, MPEG
- **Costo**: Calculado automáticamente

### Análisis de Calidad
- **Proveedor**: DeepSeek
- **Funcionalidad**: Análisis automático de transcripciones
- **Métricas**: Puntajes y recomendaciones

## Troubleshooting

### Problemas Comunes

1. **Error de permisos**
   - Verificar que el usuario esté en el grupo "Calidad"
   - Verificar asignación a la campaña "Calidad"

2. **Error de transcripción**
   - Verificar formato de audio soportado
   - Verificar configuración de API keys

3. **Error de acceso a módulo**
   - Verificar que las URLs estén incluidas
   - Verificar que la app esté en INSTALLED_APPS

### Logs y Debugging
Los logs del módulo se encuentran en la configuración estándar de Django.

## Contribución

Para contribuir al módulo:
1. Seguir las convenciones de código del proyecto
2. Documentar nuevas funcionalidades
3. Mantener compatibilidad con el sistema principal
4. Probar exhaustivamente antes de implementar

## Soporte

Para soporte técnico, contactar al equipo de desarrollo o crear un ticket en el sistema de soporte integrado.