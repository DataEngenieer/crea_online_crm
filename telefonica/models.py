from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# Opciones para estados de ventas
ESTADO_VENTA_CHOICES = [
    ('pendiente_revision', 'Pendiente de Revisión'),
    ('devuelta', 'Devuelta para Corrección'),
    ('aprobada', 'Aprobada'),
    ('digitada', 'Digitada'),
    ('rechazada', 'Rechazada'),
    ('completada', 'Completada'),
    ('cancelada', 'Cancelada'),
]

TIPO_CLIENTE_CHOICES = [
    ('nuevo', 'Nuevo'),
    ('existente', 'Existente'),
]

SEGMENTO_CHOICES = [
    ('movil', 'Móvil'),
    ('hogar', 'Hogar'),
]

TIPO_SERVICIO_CHOICES = [
    ('migracion', 'Migración'),
    ('portabilidad', 'Portabilidad'),
    ('upgrade', 'Upgrade'),
    ('television', 'Televisión'),
    ('internet', 'Internet'),
    ('telefonia_fija', 'Telefonía Fija'),
    ('combo', 'Combo'),
]


class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'CC'),
        ('CE', 'CE'),
        ('NIT', 'NIT'),
        ('PP', 'Pasaporte'),
    ]
    
    tipo_documento = models.CharField(
        max_length=10, 
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC',
        verbose_name=_("Tipo de Documento")
    )
    documento = models.CharField(max_length=20, verbose_name=_("Documento"))
    nombres = models.CharField(max_length=100, verbose_name=_("Nombres"))
    apellidos = models.CharField(max_length=100, verbose_name=_("Apellidos"))
    correo = models.EmailField(verbose_name=_("Correo Electrónico"), null=True, blank=True)
    departamento = models.CharField(max_length=100, verbose_name=_("Departamento"))
    ciudad = models.CharField(max_length=100, verbose_name=_("Ciudad"))
    barrio = models.CharField(max_length=100, verbose_name=_("Barrio"), null=True, blank=True)
    direccion = models.CharField(max_length=200, verbose_name=_("Dirección"))
    telefono = models.CharField(max_length=20, verbose_name=_("Teléfono"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.documento}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class Venta(models.Model):
    numero = models.CharField(max_length=30, verbose_name=_("Número"), null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ventas", verbose_name=_("Cliente"))
    nip = models.CharField(max_length=20, verbose_name=_("NIP"), null=True, blank=True)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, verbose_name=_("Tipo de Cliente"))
    plan_adquiere = models.CharField(max_length=100, verbose_name=_("Plan Adquirido"))
    segmento = models.CharField(max_length=20, choices=SEGMENTO_CHOICES, verbose_name=_("Segmento"))
    numero_contacto = models.CharField(max_length=20, verbose_name=_("Número de Contacto"))
    imei = models.CharField(max_length=30, verbose_name=_("IMEI"), null=True, blank=True)
    fvc = models.CharField(max_length=30, verbose_name=_("FVC"), null=True, blank=True)
    fecha_entrega = models.DateField(verbose_name=_("Fecha de Entrega"), null=True, blank=True)
    fecha_expedicion = models.DateField(verbose_name=_("Fecha de Expedición"), null=True, blank=True)
    origen = models.CharField(max_length=100, verbose_name=_("Origen"), null=True, blank=True)
    numero_grabacion = models.CharField(max_length=100, verbose_name=_("Número de Grabación"), null=True, blank=True)
    selector = models.CharField(max_length=100, verbose_name=_("Selector"), null=True, blank=True)
    orden = models.CharField(max_length=100, verbose_name=_("Orden"), null=True, blank=True)
    confronta = models.FileField(upload_to='confrontas/', verbose_name=_("Confronta"), null=True, blank=True)
    observacion = models.TextField(verbose_name=_("Observación"), null=True, blank=True)
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_realizadas", verbose_name=_("Agente"))
    revisados = models.BooleanField(default=False, verbose_name=_("Revisados"))
    estado_revisado = models.CharField(max_length=20, choices=ESTADO_VENTA_CHOICES, default='pendiente_revision', verbose_name=_("Estado Revisado"))
    observacion_2 = models.TextField(verbose_name=_("Observación 2"), null=True, blank=True)
    backoffice = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_revisadas", verbose_name=_("Backoffice"))
    hora = models.TimeField(verbose_name=_("Hora"), null=True, blank=True)
    dia = models.DateField(verbose_name=_("Día"), null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Venta")
        verbose_name_plural = _("Ventas")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Venta {self.id} - {self.cliente.nombre_completo} - {self.plan_adquiere}"
    
    def save(self, *args, **kwargs):
        # Si es una nueva venta, generar un número único
        if not self.numero:
            now = timezone.now()
            self.numero = f"TEL-{now.strftime('%Y%m%d%H%M%S')}"
            
        # Si no se especifica día/hora, usar la fecha actual
        if not self.dia:
            self.dia = timezone.now().date()
        if not self.hora:
            self.hora = timezone.now().time()
            
        super().save(*args, **kwargs)


class GestionAsesor(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="gestiones_asesor", verbose_name=_("Venta"))
    agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gestiones", verbose_name=_("Agente"))
    fecha_gestion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Gestión"))
    estado = models.CharField(max_length=20, choices=ESTADO_VENTA_CHOICES, verbose_name=_("Estado"))
    comentario = models.TextField(verbose_name=_("Comentario"))
    
    class Meta:
        verbose_name = _("Gestión de Asesor")
        verbose_name_plural = _("Gestiones de Asesores")
        ordering = ['-fecha_gestion']
    
    def __str__(self):
        return f"Gestión {self.id} - Venta {self.venta.id} - {self.agente.username}"


class GestionBackoffice(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="gestiones_backoffice", verbose_name=_("Venta"))
    backoffice = models.ForeignKey(User, on_delete=models.CASCADE, related_name="validaciones", verbose_name=_("Backoffice"))
    fecha_gestion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Gestión"))
    estado = models.CharField(max_length=20, choices=ESTADO_VENTA_CHOICES, verbose_name=_("Estado"))
    comentario = models.TextField(verbose_name=_("Comentario"))
    motivo_devolucion = models.TextField(verbose_name=_("Motivo de devolución"), null=True, blank=True)
    campos_corregir = models.TextField(verbose_name=_("Campos a corregir"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Gestión de Backoffice")
        verbose_name_plural = _("Gestiones de Backoffice")
        ordering = ['-fecha_gestion']
    
    def __str__(self):
        return f"Validación {self.id} - Venta {self.venta.id} - {self.backoffice.username}"
    
    def save(self, *args, **kwargs):
        # Si el estado es 'devuelta', actualizar el estado de la venta
        if self.estado == 'devuelta' and self.venta.estado_revisado != 'devuelta':
            self.venta.estado_revisado = 'devuelta'
            self.venta.observacion_2 = self.motivo_devolucion
            self.venta.save()
        
        # Si el estado es 'aprobada', actualizar el estado de la venta
        elif self.estado == 'aprobada' and self.venta.estado_revisado != 'aprobada':
            self.venta.estado_revisado = 'aprobada'
            self.venta.save()
            
        # Si el estado es 'digitada', actualizar el estado de la venta
        elif self.estado == 'digitada' and self.venta.estado_revisado != 'digitada':
            self.venta.estado_revisado = 'digitada'
            self.venta.save()
            
        # Si el estado es 'rechazada', actualizar el estado de la venta
        elif self.estado == 'rechazada' and self.venta.estado_revisado != 'rechazada':
            self.venta.estado_revisado = 'rechazada'
            self.venta.save()

        super().save(*args, **kwargs)


class Comision(models.Model):
    ESTADO_COMISION_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('calculada', 'Calculada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="comisiones", verbose_name=_("Venta"))
    agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comisiones", verbose_name=_("Agente"))
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Valor"))
    fecha_calculo = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Cálculo"))
    fecha_pago = models.DateField(null=True, blank=True, verbose_name=_("Fecha de Pago"))
    estado = models.CharField(max_length=20, choices=ESTADO_COMISION_CHOICES, default='pendiente', verbose_name=_("Estado"))
    observaciones = models.TextField(verbose_name=_("Observaciones"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Comisión")
        verbose_name_plural = _("Comisiones")
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f"Comisión {self.id} - Venta {self.venta.id} - {self.agente.username}"