from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os
from django.utils import timezone
from decimal import Decimal
from .utils.audio_utils import obtener_duracion_audio, obtener_tamano_archivo_mb

User = get_user_model()

def validate_audio_file_extension(value):
    import logging
    logger = logging.getLogger(__name__)
    
    # Obtener la extensión del archivo
    ext = os.path.splitext(value.name)[1]
    # Lista ampliada de extensiones válidas
    valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.mpeg', '.mpg', '.mp4', '.mp2']
    
    # Registrar información para depuración
    logger.info(f"Validando archivo de audio: {value.name} (extensión: {ext})")
    
    if not ext.lower() in valid_extensions:
        logger.warning(f"Extensión de archivo no válida: {ext}. Extensiones válidas: {valid_extensions}")
        raise ValidationError(f'Formato de archivo no soportado. Sube un archivo de audio válido (MP3, WAV, OGG, M4A, MPEG). Extensión detectada: {ext}')

class Speech(models.Model):
    auditoria = models.OneToOneField('Auditoria', on_delete=models.CASCADE, related_name='speech', null=False, blank=False)
    audio = models.FileField(upload_to='auditorias/audio/', validators=[validate_audio_file_extension])
    resultado_json = models.JSONField(blank=True, null=True, help_text="Resultado de la transcripción de Speech-to-Text")
    analisis_json = models.JSONField(blank=True, null=True, help_text="Resultado del análisis de calidad de la IA")
    transcripcion = models.CharField(max_length=255, blank=True, null=True, help_text="Ruta del archivo de transcripción JSON")
    
    # Campos para MinIO
    minio_url = models.URLField('URL de MinIO', max_length=500, blank=True, null=True, help_text="URL pública del archivo en MinIO")
    minio_object_name = models.CharField('Nombre del objeto en MinIO', max_length=255, blank=True, null=True, help_text="Nombre del archivo en MinIO")
    subido_a_minio = models.BooleanField('Subido a MinIO', default=False, help_text="Indica si el archivo fue subido exitosamente a MinIO")
    
    # Nuevos campos para métricas
    duracion_segundos = models.FloatField('Duración en segundos', default=0)
    tamano_archivo_mb = models.FloatField('Tamaño del archivo (MB)', default=0)
    tokens_procesados = models.PositiveIntegerField('Tokens procesados', null=True, blank=True)
    tiempo_procesamiento = models.FloatField('Tiempo de procesamiento (s)', null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Primero guardamos el modelo para que el archivo se guarde en el sistema de archivos
        super().save(*args, **kwargs)
        
        # Después de guardar, verificamos si hay un archivo de audio
        if self.audio:
            try:
                # Usamos self.audio.path para obtener la ruta absoluta del archivo guardado
                if hasattr(self.audio, 'path') and os.path.exists(self.audio.path):
                    # Calcular duración y tamaño del archivo
                    self.duracion_segundos = obtener_duracion_audio(self.audio.path)
                    self.tamano_archivo_mb = obtener_tamano_archivo_mb(self.audio.path)
                    
                    # Subir a MinIO si no se ha subido antes
                    if not self.subido_a_minio:
                        self._subir_audio_a_minio()
                        
                        # Si se subió exitosamente a MinIO, eliminar el archivo local
                        if self.subido_a_minio:
                            self._eliminar_archivo_local()
                    
                    # Guardar nuevamente para actualizar los campos calculados
                    super().save(update_fields=['duracion_segundos', 'tamano_archivo_mb', 'minio_url', 'minio_object_name', 'subido_a_minio', 'fecha_actualizacion'])
            except Exception as e:
                print(f"Error al procesar el archivo de audio: {e}")
    
    def _subir_audio_a_minio(self):
        """
        Método interno para subir el archivo de audio a MinIO.
        """
        try:
            from .utils.minio_utils import subir_a_minio
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Generar nombre personalizado basado en la auditoría
            nombre_personalizado = f"auditoria_{self.auditoria.id}_audio_{self.id}"
            
            # Subir archivo a MinIO
            resultado = subir_a_minio(
                archivo=self.audio,
                nombre_personalizado=nombre_personalizado,
                carpeta="audios",
                bucket_type="MINIO_BUCKET_NAME_LLAMADAS"
            )
            
            if resultado['success']:
                self.minio_url = resultado['url']
                self.minio_object_name = resultado['object_name']
                self.subido_a_minio = True
                logger.info(f"Archivo de audio subido exitosamente a MinIO: {resultado['url']}")
            else:
                logger.error(f"Error al subir archivo a MinIO: {resultado.get('error', 'Error desconocido')}")
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _subir_audio_a_minio: {str(e)}")
    
    def _eliminar_archivo_local(self):
        """
        Método interno para eliminar el archivo de audio del sistema de archivos local
        después de subirlo exitosamente a MinIO.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            if self.audio and hasattr(self.audio, 'path') and os.path.exists(self.audio.path):
                archivo_path = self.audio.path
                os.remove(archivo_path)
                logger.info(f"Archivo local eliminado exitosamente: {archivo_path}")
                
                # Limpiar la referencia del campo FileField
                self.audio = None
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al eliminar archivo local: {str(e)}")
    
    def get_audio_url(self):
        """
        Retorna la URL del archivo de audio desde MinIO únicamente.
        
        Returns:
            str: URL del archivo de audio desde MinIO
        """
        if self.subido_a_minio and self.minio_url:
            return self.minio_url
        return None
    
    def eliminar_de_minio(self):
        """
        Elimina el archivo de audio de MinIO.
        
        Returns:
            dict: Resultado de la operación
        """
        if not self.subido_a_minio or not self.minio_object_name:
            return {'success': False, 'error': 'El archivo no está en MinIO'}
        
        try:
            from .utils.minio_utils import eliminar_de_minio
            
            resultado = eliminar_de_minio(self.minio_object_name, bucket_type="MINIO_BUCKET_NAME_LLAMADAS")
            
            if resultado['success']:
                self.minio_url = None
                self.minio_object_name = None
                self.subido_a_minio = False
                self.save(update_fields=['minio_url', 'minio_object_name', 'subido_a_minio', 'fecha_actualizacion'])
            
            return resultado
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def crear_registro_uso(self, usuario):
        """
        Crea un registro de uso para facturación
        """
        from .models import UsoProcesamientoAudio
        
        # Crear el registro de uso
        uso = UsoProcesamientoAudio.objects.create(
            auditoria=self.auditoria,
            speech=self,
            usuario=usuario,
            duracion_audio_segundos=self.duracion_segundos,
            tamano_archivo_mb=self.tamano_archivo_mb
        )
        
        # Calcular costos iniciales basados en la duración
        uso.calcular_costo_transcripcion()
        uso.save()
        
        return uso
    
    def actualizar_estadisticas_transcripcion(self, tiempo_procesamiento, tokens_usados):
        """
        Actualiza las estadísticas después de la transcripción
        """
        self.tiempo_procesamiento = tiempo_procesamiento
        self.tokens_procesados = tokens_usados
        self.save(update_fields=['tiempo_procesamiento', 'tokens_procesados', 'fecha_actualizacion'])
        
        # Actualizar el registro de uso si existe
        if hasattr(self, 'uso_procesamiento'):
            self.uso_procesamiento.tiempo_transcripcion_segundos = tiempo_procesamiento
            self.uso_procesamiento.tokens_transcripcion = tokens_usados
            self.uso_procesamiento.calcular_costo_transcripcion()
            self.uso_procesamiento.save()
    
    def actualizar_estadisticas_analisis(self, tiempo_analisis, tokens_usados):
        """
        Actualiza las estadísticas después del análisis de IA
        """
        # Actualizar el registro de uso si existe
        if hasattr(self, 'uso_procesamiento'):
            self.uso_procesamiento.fecha_analisis = timezone.now()
            self.uso_procesamiento.tiempo_analisis_segundos = tiempo_analisis
            self.uso_procesamiento.tokens_analisis = tokens_usados
            self.uso_procesamiento.calcular_costo_analisis()
            self.uso_procesamiento.save()
    
    def obtener_estadisticas_procesamiento(self):
        """
        Devuelve un diccionario con las estadísticas de procesamiento
        """
        if not hasattr(self, 'uso_procesamiento'):
            return None
            
        return {
            'duracion_audio': self.uso_procesamiento.duracion_audio_segundos,
            'tamano_archivo_mb': self.uso_procesamiento.tamano_archivo_mb,
            'tiempo_transcripcion': self.uso_procesamiento.tiempo_transcripcion_segundos,
            'tokens_transcripcion': self.uso_procesamiento.tokens_transcripcion,
            'costo_transcripcion': float(self.uso_procesamiento.costo_transcripcion),
            'tiempo_analisis': self.uso_procesamiento.tiempo_analisis_segundos,
            'tokens_analisis': self.uso_procesamiento.tokens_analisis,
            'costo_analisis': float(self.uso_procesamiento.costo_analisis),
            'costo_total': float(self.uso_procesamiento.costo_total()),
        }
    
    def __str__(self):
        if self.auditoria:
            return f"Speech de Auditoría {self.auditoria.id}"
        return f"Speech {self.id} (sin auditoría)"

class MatrizCalidad(models.Model):
    """
    Modelo para definir la matriz de evaluación de calidad
    """
    # Opciones para el campo tipologia
    TIPOLOGIA_CHOICES = [
        ('atencion_telefonica', 'Atencion Telefonica'),    
        ('ofrecimiento_comercial', 'Ofrecimiento Comercial'),
        ('proceso_venta', 'Proceso de Venta'),
    ]
    
    # Campos principales
    tipologia = models.CharField(
        max_length=50,
        choices=TIPOLOGIA_CHOICES,
        verbose_name='Tipología',
        help_text='Tipo de interacción o comunicación'
    )
    
    categoria = models.CharField(
        max_length=100,
        verbose_name='Categoría',
        help_text='Nombre de la categoría del indicador'
    )
    
    indicador = models.CharField(
        max_length=255,
        verbose_name='Indicador',
        help_text='Descripción del indicador de calidad'
    )
    
    ponderacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(100)],
        verbose_name='Ponderación (%)',
        help_text='Peso del indicador en la evaluación total (0.01 - 100)'
    )
    
    # Relación con el usuario que crea/actualiza el registro
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='matrices_creadas',
        verbose_name='Usuario de Creación',
        help_text='Usuario que creó el registro'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Matriz de Calidad'
        verbose_name_plural = 'Matrices de Calidad'
        ordering = ['categoria', 'id']
    
    def __str__(self):
        return f"{self.categoria} - {self.indicador}"


class Auditoria(models.Model):
    """
    Modelo para registrar auditorías de calidad
    """
    
    TIPO_MONITOREO_CHOICES = [
        ('speech', 'Speech Analytics'),
        ('al_lado', 'Al Lado'),
        ('grabacion', 'Grabación')
    ]
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('calidad:detalle_auditoria', args=[str(self.id)])
    
    # Información del agente evaluado
    agente = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='auditorias_recibidas',
        verbose_name='Agente evaluado',
        help_text='Agente que está siendo evaluado'
    )
    
    # Información de contacto
    numero_telefono = models.CharField(
        max_length=20,
        verbose_name='Número de teléfono',
        help_text='Número de teléfono del cliente'
    )
    
    fecha_llamada = models.DateField(
        verbose_name='Fecha de la llamada',
        help_text='Fecha en que se realizó la llamada',
        default=timezone.now
    )
    
    observaciones = models.TextField(
        verbose_name='Observaciones',
        help_text='Observaciones generales de la auditoría',
        blank=True,
        null=True
    )
    
    evaluador = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='auditorias_realizadas',
        verbose_name='Evaluador',
        help_text='Persona que realiza la evaluación',
        limit_choices_to={'groups__name': 'Calidad'}
    )
    
    tipo_monitoreo = models.CharField(
        max_length=20,
        choices=TIPO_MONITOREO_CHOICES,
        verbose_name='Tipo de monitoreo',
        help_text='Tipo de monitoreo realizado'
    )
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Campos calculados
    puntaje_total = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name='Puntaje Total',
        help_text='Puntaje final de la auditoría'
    )

    observaciones_tipificacion = models.TextField(
        verbose_name='Observaciones de Tipificación',
        help_text='Detalles sobre el logueo de la llamada: tipificación, notas, etc.',
        blank=True,
        null=True
    )
    
    puntaje_ia = models.CharField(max_length=10, blank=True, null=True, help_text="Puntaje total de la evaluación de IA")
    resumen_ia = models.TextField(blank=True, null=True, help_text="Resumen de la evaluación de calidad generado por IA")
    
    # Métodos
    def __str__(self):
        return f"Auditoría de {self.agente.get_full_name()} - {self.fecha_llamada.strftime('%d/%m/%Y')}"
        
    def save(self, *args, **kwargs):
        # Si se está creando un nuevo registro y no se especificó evaluador, asignar el usuario actual
        if not self.pk and not self.evaluador_id and hasattr(self, '_current_user'):
            self.evaluador = self._current_user
            
        # Calcular el puntaje total antes de guardar
        if self.pk:  # Solo si ya existe el objeto (tiene un ID)
            self.puntaje_total = self.calcular_puntaje_total()
            
        super().save(*args, **kwargs)
    
    def calcular_puntaje_total(self):
        """
        Calcula el puntaje total de la auditoría basado en los detalles
        """
        from django.db.models import Sum, F, Case, When, DecimalField
        from decimal import Decimal

        # Si no hay respuestas, el puntaje es 0
        if not self.respuestas.exists():
            return Decimal('0.00')
            
        # Calcular la suma ponderada de los indicadores que cumplen
        resultado = self.respuestas.aggregate(
            puntaje_total=Sum(
                Case(
                    When(cumple=True, then=F('indicador__ponderacion')),
                    default=Decimal('0.00'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            ),
            total_ponderacion=Sum('indicador__ponderacion', output_field=DecimalField(max_digits=10, decimal_places=2))
        )
        
        # Si no hay ponderación total, devolver 0
        if not resultado['total_ponderacion'] or resultado['total_ponderacion'] == 0:
            return Decimal('0.00')
            
        # Calcular el porcentaje de cumplimiento
        try:
            puntaje_total = resultado['puntaje_total'] or Decimal('0.00')
            total_ponderacion = resultado['total_ponderacion']
            porcentaje = (puntaje_total / total_ponderacion) * Decimal('100.00')
            return porcentaje.quantize(Decimal('0.01'))  # Redondear a 2 decimales
        except (TypeError, ZeroDivisionError):
            return Decimal('0.00')
        
    def get_porcentaje_aprobacion(self):
        """
        Calcula el porcentaje de aprobación basado en los criterios de la empresa
        """
        from decimal import Decimal
        
        # Si no hay respuestas, el porcentaje es 0
        if not self.respuestas.exists():
            return Decimal('0.00')
            
        # Contar indicadores que cumplen
        total_indicadores = self.respuestas.count()
        indicadores_cumplen = self.respuestas.filter(cumple=True).count()
        
        # Calcular porcentaje de cumplimiento
        if total_indicadores == 0:
            return Decimal('0.00')
            
        try:
            porcentaje = (Decimal(indicadores_cumplen) / Decimal(total_indicadores)) * Decimal('100.00')
            return porcentaje.quantize(Decimal('0.01'))  # Redondear a 2 decimales
        except (TypeError, ZeroDivisionError):
            return Decimal('0.00')
        
    def get_resumen_calificacion(self):
        """
        Devuelve un resumen de la calificación con formato
        """
        from decimal import Decimal
        
        puntaje = self.calcular_puntaje_total()
        puntaje_float = float(puntaje)  # Convertir a float para la comparación
        
        if puntaje_float >= 80:
            return {
                'clase': 'success',
                'texto': f'{puntaje}% - Excelente',
                'icono': 'check-circle'
            }
        elif puntaje_float >= 60:
            return {
                'clase': 'warning',
                'texto': f'{puntaje}% - Aceptable',
                'icono': 'exclamation-circle'
            }
        else:
            return {
                'clase': 'danger',
                'texto': f'{puntaje}% - No Aceptable',
                'icono': 'times-circle'
            }
    
    def get_respuestas(self):
        """
        Devuelve un diccionario con las respuestas de los indicadores
        """
        return {respuesta.indicador_id: respuesta.cumple for respuesta in self.respuestas.all()}

    @property
    def archivo_audio(self):
        """
        Propiedad que devuelve el archivo de audio asociado a través del Speech
        """
        try:
            if hasattr(self, 'speech') and self.speech and self.speech.audio:
                return self.speech.audio
        except Speech.DoesNotExist:
            pass
        return None

    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha_llamada']
        permissions = [
            ('puede_ver_auditorias', 'Puede ver auditorías'),
            ('puede_editar_auditorias', 'Puede editar auditorías'),
            ('puede_eliminar_auditorias', 'Puede eliminar auditorías'),
        ]


class DetalleAuditoria(models.Model):
    """
    Modelo para almacenar las respuestas de los indicadores de una auditoría
    """
    auditoria = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        related_name='respuestas',
        verbose_name='Auditoría',
        help_text='Auditoría a la que pertenece esta respuesta'
    )
    
    indicador = models.ForeignKey(
        MatrizCalidad,
        on_delete=models.PROTECT,
        related_name='respuestas',
        verbose_name='Indicador',
        help_text='Indicador de calidad evaluado'
    )
    
    cumple = models.BooleanField(
        default=False,
        verbose_name='¿Cumple?',
        help_text='Indica si el indicador cumple con los estándares de calidad'
    )
    
    observaciones = models.TextField(
        verbose_name='Observaciones',
        help_text='Observaciones específicas sobre este indicador',
        blank=True,
        null=True
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'Detalle de Auditoría'
        verbose_name_plural = 'Detalles de Auditorías'
        unique_together = ('auditoria', 'indicador')
    
    def __str__(self):
        return f"{self.auditoria} - {self.indicador}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el puntaje total de la auditoría cuando se guarda un detalle
        self.auditoria.calcular_puntaje_total()


class UsoProcesamientoAudio(models.Model):
    """
    Registra el uso de los servicios de procesamiento de audio para facturación
    """
    # Relación con la auditoría que generó el consumo
    auditoria = models.OneToOneField(
        'Auditoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uso_procesamiento'
    )
    
    # Relación con el objeto Speech
    speech = models.OneToOneField(
        'Speech',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uso_procesamiento'
    )
    
    # Usuario que solicitó el procesamiento
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usos_procesamiento'
    )
    
    # Información del audio
    duracion_audio_segundos = models.FloatField(
        'Duración del audio (segundos)',
        validators=[MinValueValidator(0)],
        default=0
    )
    tamano_archivo_mb = models.FloatField(
        'Tamaño del archivo (MB)',
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # Estadísticas de la transcripción
    fecha_transcripcion = models.DateTimeField(auto_now_add=True)
    tiempo_transcripcion_segundos = models.FloatField(
        'Tiempo de transcripción (segundos)',
        null=True,
        blank=True
    )

    proveedor_transcripcion = models.CharField(
        'Proveedor de transcripción',
        max_length=50,
        default='replicate'
    )
    costo_transcripcion = models.DecimalField(
        'Costo de transcripción (USD)',
        max_digits=10,
        decimal_places=6,
        default=0
    )
    
    # Estadísticas del análisis de IA
    tokens_analisis = models.PositiveIntegerField(
        'Tokens usados en análisis',
        null=True,
        blank=True
    )
    proveedor_analisis = models.CharField(
        'Proveedor de análisis',
        max_length=50,
        default='deepseek'
    )
    costo_analisis = models.DecimalField(
        'Costo de análisis (USD)',
        max_digits=10,
        decimal_places=6,
        default=0
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Uso de Procesamiento de Audio'
        verbose_name_plural = 'Usos de Procesamiento de Audio'
        ordering = ['-fecha_transcripcion']
    
    def __str__(self):
        return f"Procesamiento para {self.auditoria} - {self.duracion_audio_segundos}s"
    
    def calcular_costo_transcripcion(self):
        """Calcula el costo de la transcripción basado en la duración del audio"""
        # Precio por segundo de audio (ajustar según tarifas del proveedor)
        PRECIO_POR_SEGUNDO = Decimal('0.0014')  # $0.0014 por segundo
        segundos = Decimal(str(self.duracion_audio_segundos))
        self.costo_transcripcion = (segundos * PRECIO_POR_SEGUNDO).quantize(Decimal('0.000001'))
        return self.costo_transcripcion
    
    def calcular_costo_analisis(self):
        """Calcula el costo del análisis basado en los tokens usados"""
        # Precio por 1K tokens (ajustar según tarifas del proveedor)
        PRECIO_POR_MIL_TOKENS = Decimal('0.02')  # $0.02 por 1K tokens
        if self.tokens_analisis:
            miles_de_tokens = Decimal(str(self.tokens_analisis)) / Decimal('1000')
            self.costo_analisis = (miles_de_tokens * PRECIO_POR_MIL_TOKENS).quantize(Decimal('0.000001'))
        return self.costo_analisis or Decimal('0')
    
    def costo_total(self):
        """Retorna el costo total del procesamiento"""
        return (self.costo_transcripcion or Decimal('0')) + (self.costo_analisis or Decimal('0'))


class RespuestaAuditoria(models.Model):
    """
    Modelo para manejar las respuestas de los asesores a los indicadores no cumplidos
    en las auditorías, permitiendo compromisos de mejora y trazabilidad.
    """
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de respuesta'),
        ('respondido', 'Respondido'),
        ('en_seguimiento', 'En seguimiento'),
        ('cerrado', 'Cerrado'),
    ]
    
    TIPO_RESPUESTA_CHOICES = [
        ('compromiso_mejora', 'Compromiso de mejora'),
        ('aclaracion', 'Aclaración'),
        ('plan_accion', 'Plan de acción'),
        ('capacitacion', 'Solicitud de capacitación'),
    ]
    
    # Relación con la auditoría
    auditoria = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        related_name='respuestas_asesor',
        verbose_name='Auditoría',
        help_text='Auditoría a la que pertenece esta respuesta'
    )
    
    # Relación con el detalle específico (indicador no cumplido)
    detalle_auditoria = models.ForeignKey(
        DetalleAuditoria,
        on_delete=models.CASCADE,
        related_name='respuestas_asesor',
        verbose_name='Detalle de Auditoría',
        help_text='Indicador específico al que se está respondiendo'
    )
    
    # Usuario que responde (debe ser el mismo agente de la auditoría)
    asesor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='respuestas_auditoria',
        verbose_name='Asesor',
        help_text='Asesor que proporciona la respuesta'
    )
    
    # Tipo de respuesta
    tipo_respuesta = models.CharField(
        max_length=20,
        choices=TIPO_RESPUESTA_CHOICES,
        verbose_name='Tipo de respuesta',
        help_text='Categoría de la respuesta del asesor'
    )
    
    # Contenido de la respuesta
    respuesta = models.TextField(
        verbose_name='Respuesta del asesor',
        help_text='Explicación, compromiso o plan de acción del asesor'
    )
    
    # Compromiso específico
    compromiso = models.TextField(
        verbose_name='Compromiso de mejora',
        help_text='Compromiso específico del asesor para mejorar en este indicador',
        blank=True,
        null=True
    )
    
    # Fecha límite para el compromiso
    fecha_compromiso = models.DateField(
        verbose_name='Fecha límite del compromiso',
        help_text='Fecha en la que el asesor se compromete a implementar la mejora',
        blank=True,
        null=True
    )
    
    # Estado de la respuesta
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado',
        help_text='Estado actual de la respuesta'
    )
    
    # Campos de trazabilidad
    fecha_respuesta = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de respuesta'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Seguimiento por parte del evaluador
    comentario_evaluador = models.TextField(
        verbose_name='Comentario del evaluador',
        help_text='Comentarios del evaluador sobre la respuesta del asesor',
        blank=True,
        null=True
    )
    
    evaluador_seguimiento = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='seguimientos_respuestas',
        verbose_name='Evaluador de seguimiento',
        help_text='Evaluador que hace seguimiento a la respuesta',
        blank=True,
        null=True
    )
    
    fecha_seguimiento = models.DateTimeField(
        verbose_name='Fecha de seguimiento',
        help_text='Fecha del último seguimiento por parte del evaluador',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Respuesta de Auditoría'
        verbose_name_plural = 'Respuestas de Auditorías'
        unique_together = ('auditoria', 'detalle_auditoria', 'asesor')
        ordering = ['-fecha_respuesta']
    
    def __str__(self):
        return f"Respuesta de {self.asesor.get_full_name() or self.asesor.username} - {self.auditoria} - {self.detalle_auditoria.indicador.indicador[:50]}"
    
    def save(self, *args, **kwargs):
        # Validar que el asesor sea el mismo agente de la auditoría
        if self.asesor != self.auditoria.agente:
            raise ValidationError('El asesor debe ser el mismo agente evaluado en la auditoría')
        
        # Validar que el detalle pertenezca a la auditoría
        if self.detalle_auditoria.auditoria != self.auditoria:
            raise ValidationError('El detalle de auditoría debe pertenecer a la auditoría especificada')
        
        # Validar que el indicador no cumpla (solo se puede responder a indicadores no cumplidos)
        if self.detalle_auditoria.cumple:
            raise ValidationError('Solo se puede responder a indicadores que no cumplan')
        
        # Actualizar estado automáticamente
        if self.respuesta and self.estado == 'pendiente':
            self.estado = 'respondido'
        
        super().save(*args, **kwargs)
    
    def marcar_en_seguimiento(self, evaluador, comentario=None):
        """
        Marca la respuesta como en seguimiento por parte del evaluador
        """
        self.estado = 'en_seguimiento'
        self.evaluador_seguimiento = evaluador
        self.fecha_seguimiento = timezone.now()
        if comentario:
            self.comentario_evaluador = comentario
        self.save()
    
    def cerrar_respuesta(self, evaluador, comentario=None):
        """
        Cierra la respuesta indicando que se ha completado el seguimiento
        """
        self.estado = 'cerrado'
        self.evaluador_seguimiento = evaluador
        self.fecha_seguimiento = timezone.now()
        if comentario:
            self.comentario_evaluador = comentario
        self.save()
    
    @property
    def dias_desde_respuesta(self):
        """
        Calcula los días transcurridos desde la respuesta
        """
        return (timezone.now().date() - self.fecha_respuesta.date()).days
    
    @property
    def dias_hasta_compromiso(self):
        """
        Calcula los días restantes hasta la fecha de compromiso
        """
        if self.fecha_compromiso:
            return (self.fecha_compromiso - timezone.now().date()).days
        return None
    
    @property
    def compromiso_vencido(self):
        """
        Indica si el compromiso está vencido
        """
        if self.fecha_compromiso:
            return timezone.now().date() > self.fecha_compromiso
        return False