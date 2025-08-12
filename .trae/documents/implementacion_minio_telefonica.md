# Implementación de MinIO para Archivos Adjuntos en Ventas de Telefónica

## 1. Análisis de la Situación Actual

### 1.1 Estado Actual
Actualmente, las ventas de Telefónica manejan archivos adjuntos (principalmente el campo `confronta` en `VentaPortabilidad`) que se almacenan localmente usando el sistema de archivos de Django con `FileField`.

### 1.2 Implementación Existente de MinIO
El módulo de `calidad` ya tiene una implementación completa de MinIO que incluye:
- Utilidades en `calidad/utils/minio_utils.py`
- Configuración de buckets en `settings.py`
- Integración automática en modelos (`Speech`)
- Funciones de subida, descarga y eliminación

### 1.3 Configuración Disponible
En `settings.py` ya existe la configuración del bucket para Telefónica:
```python
"MINIO_BUCKET_NAME_TELEFONICA":"telefonica-crea-online"
```

## 2. Modelos que Requieren Modificación

### 2.1 VentaPortabilidad
**Archivo:** `telefonica/models.py`

**Campos actuales relacionados con archivos:**
- `confronta = models.FileField(upload_to='confrontas/', verbose_name=_("Confronta"), null=True, blank=True)`

**Campos a agregar:**
```python
# Campos para integración con MinIO
confronta_minio_url = models.URLField(verbose_name=_("URL MinIO Confronta"), null=True, blank=True)
confronta_minio_object_name = models.CharField(max_length=500, verbose_name=_("Nombre Objeto MinIO Confronta"), null=True, blank=True)
confronta_subido_a_minio = models.BooleanField(default=False, verbose_name=_("Confronta Subido a MinIO"))
```

**Métodos a agregar:**
```python
def _subir_confronta_a_minio(self):
    """
    Método interno para subir el archivo confronta a MinIO.
    Basado en la implementación de Speech._subir_audio_a_minio()
    """
    try:
        from calidad.utils.minio_utils import subir_a_minio
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Generar nombre personalizado basado en la venta
        nombre_personalizado = f"venta_{self.numero}_confronta_{self.id}"
        logger.info(f"[MINIO-UPLOAD-TELEFONICA] Nombre personalizado: {nombre_personalizado}")
        logger.info(f"[MINIO-UPLOAD-TELEFONICA] Archivo a subir: {self.confronta.name}")
        
        # Subir archivo a MinIO usando el bucket de Telefónica
        resultado = subir_a_minio(
            archivo=self.confronta,
            nombre_personalizado=nombre_personalizado,
            carpeta="confrontas",
            bucket_type="MINIO_BUCKET_NAME_TELEFONICA"
        )
        
        logger.info(f"[MINIO-UPLOAD-TELEFONICA] Resultado de subida: {resultado}")
        
        if resultado['success']:
            self.confronta_minio_url = resultado['url']
            self.confronta_minio_object_name = resultado['object_name']
            self.confronta_subido_a_minio = True
            logger.info(f"[MINIO-UPLOAD-TELEFONICA] ✅ Archivo confronta subido exitosamente: {resultado['url']}")
            
            # Guardar cambios en la base de datos
            self.save(update_fields=['confronta_minio_url', 'confronta_minio_object_name', 'confronta_subido_a_minio'])
            
            # Eliminar archivo local después de subida exitosa
            self._eliminar_confronta_local()
        else:
            logger.error(f"[MINIO-UPLOAD-TELEFONICA] ❌ Error al subir confronta: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        logger.error(f"[MINIO-UPLOAD-TELEFONICA] ❌ Excepción al subir confronta: {str(e)}")

def _eliminar_confronta_local(self):
    """
    Elimina el archivo confronta local después de subida exitosa a MinIO.
    """
    try:
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        if self.confronta and os.path.exists(self.confronta.path):
            os.remove(self.confronta.path)
            logger.info(f"[MINIO-UPLOAD-TELEFONICA] Archivo local eliminado: {self.confronta.path}")
            # Limpiar el campo confronta
            self.confronta = None
            self.save(update_fields=['confronta'])
        
    except Exception as e:
        logger.error(f"[MINIO-UPLOAD-TELEFONICA] Error al eliminar archivo local: {str(e)}")

def eliminar_confronta_de_minio(self):
    """
    Elimina el archivo confronta de MinIO.
    """
    if not self.confronta_subido_a_minio or not self.confronta_minio_object_name:
        return {'success': False, 'error': 'El archivo no está en MinIO'}
    
    try:
        from calidad.utils.minio_utils import eliminar_de_minio
        
        resultado = eliminar_de_minio(
            object_name=self.confronta_minio_object_name,
            bucket_type="MINIO_BUCKET_NAME_TELEFONICA"
        )
        
        if resultado['success']:
            # Limpiar campos de MinIO
            self.confronta_minio_url = None
            self.confronta_minio_object_name = None
            self.confronta_subido_a_minio = False
            self.save(update_fields=['confronta_minio_url', 'confronta_minio_object_name', 'confronta_subido_a_minio'])
        
        return resultado
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def obtener_url_descarga_confronta(self, expiry_days=7):
    """
    Genera una URL de descarga temporal para el archivo confronta.
    """
    if not self.confronta_subido_a_minio or not self.confronta_minio_object_name:
        return None
    
    try:
        from calidad.utils.minio_utils import obtener_url_descarga
        
        return obtener_url_descarga(
            object_name=self.confronta_minio_object_name,
            expiry_days=expiry_days,
            bucket_type="MINIO_BUCKET_NAME_TELEFONICA"
        )
        
    except Exception as e:
        return None
```

**Modificación del método save():**
```python
def save(self, *args, **kwargs):
    # Lógica existente...
    if not self.numero:
        now = timezone.now()
        self.numero = f"PORTA-{now.strftime('%Y%m%d%H%M%S')}"
    
    # Guardar información del plan de forma permanente
    if self.plan_adquiere and not self.plan_nombre:
        self.plan_nombre = self.plan_adquiere.nombre_plan
        self.plan_codigo = self.plan_adquiere.codigo
        self.plan_caracteristicas = self.plan_adquiere.caracteristicas
        self.plan_cfm = self.plan_adquiere.CFM
        self.plan_cfm_sin_iva = self.plan_adquiere.CFM_sin_iva
    
    # NUEVA LÓGICA: Subir confronta a MinIO si existe y no está subido
    is_new = self.pk is None
    
    super().save(*args, **kwargs)
    
    # Subir confronta a MinIO después de guardar el objeto
    if self.confronta and not self.confronta_subido_a_minio:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[VENTA-SAVE-TELEFONICA] Iniciando subida de confronta a MinIO...")
        self._subir_confronta_a_minio()
```

## 3. Migración de Base de Datos

**Archivo:** `telefonica/migrations/XXXX_add_minio_fields.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('telefonica', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='ventaportabilidad',
            name='confronta_minio_url',
            field=models.URLField(blank=True, null=True, verbose_name='URL MinIO Confronta'),
        ),
        migrations.AddField(
            model_name='ventaportabilidad',
            name='confronta_minio_object_name',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Nombre Objeto MinIO Confronta'),
        ),
        migrations.AddField(
            model_name='ventaportabilidad',
            name='confronta_subido_a_minio',
            field=models.BooleanField(default=False, verbose_name='Confronta Subido a MinIO'),
        ),
    ]
```

## 4. Modificaciones en Templates

### 4.1 Template de Detalle de Venta
**Archivo:** `telefonica/templates/telefonica/venta_detalle.html`

**Modificación en la sección de confronta:**
```html
<!-- Sección de Confronta -->
<div class="row mb-3">
    <div class="col-md-6">
        <strong>Confronta:</strong>
        {% if venta.confronta_subido_a_minio and venta.confronta_minio_url %}
            <!-- Archivo en MinIO -->
            <a href="{% url 'telefonica:descargar_confronta' venta.id %}" class="btn btn-sm btn-outline-primary" target="_blank">
                <i class="fas fa-download"></i> Descargar Confronta
            </a>
            <small class="text-muted d-block">Archivo almacenado en MinIO</small>
        {% elif venta.confronta %}
            <!-- Archivo local (legacy) -->
            <a href="{{ venta.confronta.url }}" class="btn btn-sm btn-outline-primary" target="_blank">
                <i class="fas fa-download"></i> Descargar Confronta
            </a>
            <small class="text-muted d-block">Archivo local</small>
        {% else %}
            <span class="text-muted">No disponible</span>
        {% endif %}
    </div>
</div>
```

### 4.2 Template de Corrección de Venta
**Archivo:** `telefonica/templates/telefonica/venta_corregir.html`

**Modificación en la sección de confronta:**
```html
<div class="form-group">
    <label for="id_confronta">Confronta (documento de validación):</label>
    {{ form.confronta }}
    <div class="invalid-feedback" id="confronta-error"></div>
    {% if venta.confronta_subido_a_minio and venta.confronta_minio_url %}
        <small class="form-text text-success">
            Ya existe un archivo en MinIO. 
            <a href="{% url 'telefonica:descargar_confronta' venta.id %}" target="_blank">Ver confronta actual</a>
            <br>Sólo seleccione uno nuevo si desea reemplazarlo.
        </small>
    {% elif venta.confronta %}
        <small class="form-text text-info">
            Ya existe un archivo cargado (local). 
            <a href="{{ venta.confronta.url }}" target="_blank">Ver confronta actual</a>
            <br>Sólo seleccione uno nuevo si desea reemplazarlo.
        </small>
    {% else %}
        <small class="form-text text-muted">Seleccione el archivo de confronta si está disponible</small>
    {% endif %}
</div>
```

## 5. Modificaciones en Vistas

### 5.1 Nueva Vista para Descarga de Confronta
**Archivo:** `telefonica/views.py`

```python
@login_required
def descargar_confronta(request, venta_id):
    """
    Vista para descargar archivo confronta desde MinIO.
    Genera URL temporal de descarga.
    """
    venta = get_object_or_404(VentaPortabilidad, id=venta_id)
    
    # Verificar permisos: solo el agente propietario, backoffice o admin
    if not (venta.agente == request.user or 
            request.user.groups.filter(name='backoffice').exists() or 
            request.user.groups.filter(name__iexact='Administrador').exists() or 
            request.user.is_superuser):
        return HttpResponseForbidden("No tienes permiso para descargar este archivo")
    
    # Verificar que el archivo esté en MinIO
    if not venta.confronta_subido_a_minio or not venta.confronta_minio_object_name:
        messages.error(request, 'El archivo confronta no está disponible en MinIO')
        return redirect('telefonica:detalle_venta_portabilidad', pk=venta.id)
    
    # Obtener URL de descarga temporal
    url_descarga = venta.obtener_url_descarga_confronta(expiry_days=1)  # 1 día de validez
    
    if url_descarga:
        return redirect(url_descarga)
    else:
        messages.error(request, 'Error al generar URL de descarga')
        return redirect('telefonica:detalle_venta_portabilidad', pk=venta.id)

@login_required
def resubir_confronta_minio(request, venta_id):
    """
    Vista para forzar la subida de un archivo confronta a MinIO.
    Útil para migrar archivos existentes.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        venta = get_object_or_404(VentaPortabilidad, id=venta_id)
        
        # Verificar permisos
        if not (request.user.groups.filter(name='backoffice').exists() or 
                request.user.groups.filter(name__iexact='Administrador').exists() or 
                request.user.is_superuser):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Verificar que existe archivo local
        if not venta.confronta:
            return JsonResponse({'error': 'No hay archivo confronta para subir'}, status=400)
        
        # Forzar subida a MinIO
        venta._subir_confronta_a_minio()
        
        if venta.confronta_subido_a_minio:
            return JsonResponse({
                'success': True, 
                'message': 'Archivo subido exitosamente a MinIO',
                'url': venta.confronta_minio_url
            })
        else:
            return JsonResponse({'error': 'Error al subir archivo a MinIO'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

### 5.2 Modificación en Vista de Corrección
**Archivo:** `telefonica/views.py` - función `venta_corregir`

```python
# En la función venta_corregir, después de form.is_valid():
if form.is_valid():
    venta = form.save(commit=False)
    venta.estado_venta = 'pendiente_revision'
    
    # NUEVA LÓGICA: Manejar archivo confronta actualizado
    if 'confronta' in form.changed_data and venta.confronta:
        # Si se subió un nuevo archivo, eliminar el anterior de MinIO
        if venta.confronta_subido_a_minio:
            venta.eliminar_confronta_de_minio()
        
        # Resetear campos de MinIO para que se suba el nuevo archivo
        venta.confronta_subido_a_minio = False
        venta.confronta_minio_url = None
        venta.confronta_minio_object_name = None
    
    venta.save()  # Esto activará la subida automática a MinIO
    
    # Resto de la lógica existente...
```

## 6. Modificaciones en URLs

**Archivo:** `telefonica/urls.py`

```python
# Agregar estas URLs al urlpatterns existente:
path('venta/<int:venta_id>/descargar-confronta/', views.descargar_confronta, name='descargar_confronta'),
path('venta/<int:venta_id>/resubir-confronta-minio/', views.resubir_confronta_minio, name='resubir_confronta_minio'),
```

## 7. Comando de Migración para Archivos Existentes

**Archivo:** `telefonica/management/commands/migrar_confrontas_minio.py`

```python
from django.core.management.base import BaseCommand
from django.db import transaction
from telefonica.models import VentaPortabilidad
import logging

class Command(BaseCommand):
    help = 'Migra archivos confronta existentes a MinIO'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo de prueba sin hacer cambios reales',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Límite de archivos a procesar por ejecución',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        logger = logging.getLogger(__name__)
        
        # Buscar ventas con confronta local pero no subido a MinIO
        ventas_pendientes = VentaPortabilidad.objects.filter(
            confronta__isnull=False,
            confronta_subido_a_minio=False
        )[:limit]
        
        total_ventas = ventas_pendientes.count()
        self.stdout.write(f"Encontradas {total_ventas} ventas con confronta pendiente de migrar")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se realizarán cambios reales"))
            for venta in ventas_pendientes:
                self.stdout.write(f"  - Venta {venta.numero}: {venta.confronta.name}")
            return
        
        exitosos = 0
        errores = 0
        
        for venta in ventas_pendientes:
            try:
                with transaction.atomic():
                    self.stdout.write(f"Procesando venta {venta.numero}...")
                    venta._subir_confronta_a_minio()
                    
                    if venta.confronta_subido_a_minio:
                        exitosos += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✅ Venta {venta.numero} migrada exitosamente")
                        )
                    else:
                        errores += 1
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error al migrar venta {venta.numero}")
                        )
                        
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Excepción al procesar venta {venta.numero}: {str(e)}")
                )
        
        self.stdout.write(f"\nResumen de migración:")
        self.stdout.write(f"  - Exitosos: {exitosos}")
        self.stdout.write(f"  - Errores: {errores}")
        self.stdout.write(f"  - Total procesados: {exitosos + errores}")
```

## 8. Consideraciones de Seguridad y Rendimiento

### 8.1 Validaciones de Archivo
- Mantener las validaciones existentes de tipo y tamaño de archivo
- Agregar validación de virus si es necesario
- Limitar tipos de archivo permitidos

### 8.2 Manejo de Errores
- Implementar retry automático en caso de falla de subida
- Mantener archivo local como respaldo hasta confirmar subida exitosa
- Logging detallado para troubleshooting

### 8.3 Rendimiento
- Subida asíncrona usando Celery (opcional, para implementación futura)
- Compresión de archivos antes de subida
- Limpieza automática de archivos temporales

## 9. Plan de Implementación

### Fase 1: Preparación
1. Crear migración de base de datos
2. Ejecutar migración en entorno de desarrollo
3. Probar funcionalidad básica

### Fase 2: Implementación
1. Modificar modelo VentaPortabilidad
2. Actualizar templates
3. Modificar vistas
4. Agregar URLs

### Fase 3: Migración
1. Crear comando de migración
2. Probar migración con datos de prueba
3. Ejecutar migración en producción por lotes

### Fase 4: Validación
1. Verificar funcionamiento completo
2. Monitorear logs de errores
3. Validar integridad de archivos

## 10. Comandos de Ejecución

```bash
# Crear y ejecutar migración
python manage.py makemigrations telefonica
python manage.py migrate

# Migrar archivos existentes (modo prueba)
python manage.py migrar_confrontas_minio --dry-run

# Migrar archivos existentes (real)
python manage.py migrar_confrontas_minio --limit 50
```

## 11. Monitoreo y Mantenimiento

### 11.1 Logs a Monitorear
- Subidas exitosas y fallidas
- Eliminaciones de archivos
- Generación de URLs de descarga

### 11.2 Métricas Importantes
- Porcentaje de archivos en MinIO vs local
- Tiempo promedio de subida
- Errores de conectividad con MinIO

### 11.3 Tareas de Mantenimiento
- Limpieza periódica de archivos huérfanos
- Verificación de integridad de archivos
- Rotación de logs de MinIO

Esta implementación garantiza una integración completa y segura de MinIO para los archivos adjuntos en las ventas de Telefónica, manteniendo la compatibilidad con el sistema existente y proporcionando una ruta de migración clara para los archivos actuales.