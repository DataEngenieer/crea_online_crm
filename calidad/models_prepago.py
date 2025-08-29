from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from decimal import Decimal

User = get_user_model()

class MatrizCalidadPrepago(models.Model):
    """
    Modelo para definir la matriz de evaluación de calidad específica para campaña Prepago
    """
    # Opciones para el campo tipologia - sincronizadas con modelo principal
    TIPOLOGIA_CHOICES = [
        ('ECUF', 'ECUF'),    
        ('ECN', 'ECN'),
        ('Estadistico', 'Estadístico'),
    ]
    
    # Campos principales
    tipologia = models.CharField(
        max_length=50,
        choices=TIPOLOGIA_CHOICES,
        verbose_name='Tipología Prepago',
        help_text='Tipo de interacción específica para servicios prepago'
    )
    
    categoria = models.CharField(
        max_length=100,
        verbose_name='Categoría',
        help_text='Nombre de la categoría del indicador para prepago'
    )
    
    indicador = models.CharField(
        max_length=255,
        verbose_name='Indicador',
        help_text='Descripción del indicador de calidad para prepago'
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
        related_name='matrices_prepago_creadas',
        verbose_name='Usuario de Creación',
        help_text='Usuario que creó el registro'
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Matriz de Calidad Prepago'
        verbose_name_plural = 'Matrices de Calidad Prepago'
        ordering = ['categoria', 'id']
    
    def __str__(self):
        return f"Prepago - {self.categoria} - {self.indicador}"


class AuditoriaPrepago(models.Model):
    """
    Modelo para registrar auditorías de calidad específicas para campaña Prepago
    """
    
    TIPO_MONITOREO_CHOICES = [
        ('speech', 'Speech Analytics'),
        ('grabacion', 'Grabación')
    ]
    
    def get_absolute_url(self):
        return reverse('calidad:detalle_auditoria_prepago', args=[str(self.id)])
    
    # Información del agente evaluado
    agente = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='auditorias_prepago_recibidas',
        verbose_name='Agente evaluado',
        help_text='Agente que está siendo evaluado en campaña prepago'
    )
    
    # Información de contacto
    numero_telefono = models.CharField(
        max_length=20,
        verbose_name='Número de teléfono',
        help_text='Número de teléfono del cliente prepago'
    )
    
    fecha_llamada = models.DateField(
        verbose_name='Fecha de la llamada',
        help_text='Fecha en que se realizó la llamada prepago',
        default=timezone.now
    )
    
    observaciones = models.TextField(
        verbose_name='Observaciones',
        help_text='Observaciones generales de la auditoría prepago',
        blank=True,
        null=True
    )
    
    evaluador = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='auditorias_prepago_realizadas',
        verbose_name='Evaluador',
        help_text='Persona que realiza la evaluación prepago',
        limit_choices_to={'groups__name': 'Calidad'}
    )
    
    tipo_monitoreo = models.CharField(
        max_length=20,
        choices=TIPO_MONITOREO_CHOICES,
        verbose_name='Tipo de monitoreo',
        help_text='Tipo de monitoreo realizado para prepago'
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
        help_text='Puntaje final de la auditoría prepago'
    )

    observaciones_tipificacion = models.TextField(
        verbose_name='Observaciones de Tipificación',
        help_text='Detalles sobre el logueo de la llamada prepago: tipificación, notas, etc.',
        blank=True,
        null=True
    )
    
    puntaje_ia = models.CharField(max_length=10, blank=True, null=True, help_text="Puntaje total de la evaluación de IA para prepago")
    resumen_ia = models.TextField(blank=True, null=True, help_text="Resumen de la evaluación de calidad generado por IA para prepago")
    
    def calcular_puntaje_total(self):
        """
        Calcula el puntaje total de la auditoría basado en las respuestas de los indicadores
        """
        respuestas = self.respuestas_prepago.all()
        if not respuestas.exists():
            self.puntaje_total = Decimal('0.00')
            self.save(update_fields=['puntaje_total'])
            return self.puntaje_total
        
        puntaje_obtenido = Decimal('0.00')
        puntaje_total_posible = Decimal('0.00')
        
        for respuesta in respuestas:
            ponderacion = respuesta.indicador.ponderacion
            puntaje_total_posible += ponderacion
            
            if respuesta.cumple:
                puntaje_obtenido += ponderacion
        
        # Calcular porcentaje
        if puntaje_total_posible > 0:
            porcentaje = (puntaje_obtenido / puntaje_total_posible) * 100
            self.puntaje_total = porcentaje.quantize(Decimal('0.01'))
        else:
            self.puntaje_total = Decimal('0.00')
        
        self.save(update_fields=['puntaje_total'])
        return self.puntaje_total
    
    def get_color_puntaje(self):
        """
        Retorna el color CSS basado en el puntaje total
        """
        if self.puntaje_total >= 90:
            return 'success'  # Verde
        elif self.puntaje_total >= 80:
            return 'warning'  # Amarillo
        else:
            return 'danger'   # Rojo
    
    def get_estado_puntaje(self):
        """
        Retorna el estado textual basado en el puntaje
        """
        if self.puntaje_total >= 90:
            return 'Excelente'
        elif self.puntaje_total >= 80:
            return 'Bueno'
        elif self.puntaje_total >= 70:
            return 'Regular'
        else:
            return 'Deficiente'
    
    def get_indicadores_no_cumplidos(self):
        """
        Retorna los indicadores que no fueron cumplidos en esta auditoría
        """
        return self.respuestas_prepago.filter(cumple=False)
    
    def tiene_respuestas_pendientes(self):
        """
        Verifica si hay indicadores no cumplidos sin respuesta del asesor
        """
        indicadores_no_cumplidos = self.get_indicadores_no_cumplidos()
        for detalle in indicadores_no_cumplidos:
            if not hasattr(detalle, 'respuesta_asesor') or detalle.respuesta_asesor is None:
                return True
        return False
    
    class Meta:
        verbose_name = 'Auditoría Prepago'
        verbose_name_plural = 'Auditorías Prepago'
        ordering = ['-fecha_llamada']
        permissions = [
            ('puede_ver_auditorias_prepago', 'Puede ver auditorías prepago'),
            ('puede_editar_auditorias_prepago', 'Puede editar auditorías prepago'),
            ('puede_eliminar_auditorias_prepago', 'Puede eliminar auditorías prepago'),
        ]
    
    def __str__(self):
        return f"Auditoría Prepago {self.id} - {self.agente.get_full_name() or self.agente.username} - {self.fecha_llamada}"


class DetalleAuditoriaPrepago(models.Model):
    """
    Modelo para almacenar las respuestas de los indicadores de una auditoría prepago
    """
    auditoria = models.ForeignKey(
        AuditoriaPrepago,
        on_delete=models.CASCADE,
        related_name='respuestas_prepago',
        verbose_name='Auditoría Prepago',
        help_text='Auditoría prepago a la que pertenece esta respuesta'
    )
    
    indicador = models.ForeignKey(
        MatrizCalidadPrepago,
        on_delete=models.PROTECT,
        related_name='respuestas_prepago',
        verbose_name='Indicador Prepago',
        help_text='Indicador de calidad prepago evaluado'
    )
    
    cumple = models.BooleanField(
        default=False,
        verbose_name='¿Cumple?',
        help_text='Indica si el indicador cumple con los estándares de calidad prepago'
    )
    
    observaciones = models.TextField(
        verbose_name='Observaciones',
        help_text='Observaciones específicas sobre este indicador prepago',
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
        verbose_name = 'Detalle de Auditoría Prepago'
        verbose_name_plural = 'Detalles de Auditorías Prepago'
        unique_together = ('auditoria', 'indicador')
    
    def __str__(self):
        return f"{self.auditoria} - {self.indicador}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar el puntaje total de la auditoría cuando se guarda un detalle
        self.auditoria.calcular_puntaje_total()


class RespuestaAuditoriaPrepago(models.Model):
    """
    Modelo para almacenar las respuestas de los asesores a indicadores no cumplidos en auditorías prepago
    """
    
    TIPO_RESPUESTA_CHOICES = [
        ('explicacion', 'Explicación'),
        ('desacuerdo', 'Desacuerdo'),
        ('plan_mejora', 'Plan de Mejora'),
        ('capacitacion', 'Solicitud de Capacitación'),
        ('aclaracion', 'Solicitud de Aclaración'),
    ]
    
    # Relaciones
    auditoria = models.ForeignKey(
        AuditoriaPrepago,
        on_delete=models.CASCADE,
        related_name='respuestas_asesor_prepago',
        verbose_name='Auditoría Prepago'
    )
    
    detalle_auditoria = models.OneToOneField(
        DetalleAuditoriaPrepago,
        on_delete=models.CASCADE,
        related_name='respuesta_asesor_prepago',
        verbose_name='Detalle de Auditoría Prepago'
    )
    
    asesor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='respuestas_auditorias_prepago',
        verbose_name='Asesor'
    )
    
    # Campos de respuesta
    tipo_respuesta = models.CharField(
        max_length=20,
        choices=TIPO_RESPUESTA_CHOICES,
        verbose_name='Tipo de respuesta'
    )
    
    respuesta = models.TextField(
        verbose_name='Respuesta',
        help_text='Respuesta detallada del asesor'
    )
    
    compromiso = models.TextField(
        verbose_name='Compromiso de mejora',
        help_text='Compromiso específico de mejora (opcional)',
        blank=True,
        null=True
    )
    
    fecha_compromiso = models.DateField(
        verbose_name='Fecha límite del compromiso',
        help_text='Fecha en la que se compromete a implementar la mejora',
        blank=True,
        null=True
    )
    
    # Campos de control
    fecha_respuesta = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de respuesta'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'Respuesta de Auditoría Prepago'
        verbose_name_plural = 'Respuestas de Auditorías Prepago'
        ordering = ['-fecha_respuesta']
    
    def __str__(self):
        return f"Respuesta de {self.asesor.get_full_name()} - Auditoría Prepago {self.auditoria.id}"