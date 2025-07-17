from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# Opciones para estados de ventas
ESTADO_VENTA_CHOICES = [
    ('pendiente_revision', 'Pendiente de Revisión'),
    ('escalamiento', 'Escalamiento'),
    ('cliente_confirma', 'Cliente Confirma'),
    ('cliente_no_confirma', 'Cliente No Confirma'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
    ('escalamiento_no_solucionado', 'No Solucionado'),
    ('venta_con_escalamiento', 'Venta con Escalamiento'),
]

ESTADO_LOGISTICA_CHOICES = [
    ('pendiente_seguimiento', 'Pendiente de Seguimiento'),
    ('en_transito', 'En Transito'),
    ('entregado', 'Entregado'),
    ('rechazado', 'Rechazado'),
]

TIPO_CLIENTE_CHOICES = [
    ('dentro_base', 'Dentro de la Base'),
    ('fuera_base', 'Fuera de la Base'),
]

ESTADO_CHOICES = [
    ('activo', 'Activo'),
    ('inactivo', 'Inactivo'),
]

ESTADO_AGENDAMIENTO_CHOICES = [
    ('agendado', 'Agendado'),
    ('venta', 'Venta'),
    ('no_venta', 'No Venta'),
]

class Planes_portabilidad(models.Model):
    """Modelo para controlar los planes disponibles para venta"""
    codigo = models.CharField(max_length=50, unique=True, verbose_name=_("Código"))
    nombre_plan = models.CharField(max_length=150, verbose_name=_("Nombre del Plan"))
    caracteristicas = models.TextField(verbose_name=_("Características"), null=False, blank=False)
    CFM = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Cargo Fijo Mensual"))
    CFM_sin_iva = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Cargo Fijo Mensual sin IVA"))
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name=_("Estado"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    tipo_plan = models.CharField(max_length=20, choices=[('portabilidad', 'Portabilidad'), ('prepos', 'PrePos'),('upgrade', 'Upgrade')], default='portabilidad', verbose_name=_("Tipo de Plan"))
    
    class Meta:
        verbose_name = _("Plan")
        verbose_name_plural = _("Planes")
        ordering = ['nombre_plan']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre_plan}"

class VentaPortabilidad(models.Model):

    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'CC'),
        ('CE', 'CE'),
        ('NIT', 'NIT'),
        ('PP', 'Pasaporte'),
    ]

    numero = models.CharField(verbose_name=_("Número"), null=False, blank=False)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, verbose_name=_("Tipo de Cliente"))

    tipo_documento = models.CharField(
        max_length=10, 
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC',
        verbose_name=_("Tipo de Documento")
    )

    documento = models.CharField(max_length=15, verbose_name=_("Documento"), null=False)
    fecha_expedicion = models.DateField(verbose_name=_("Fecha de Expedición"), null=False)
    nombres = models.CharField(max_length=100, verbose_name=_("Nombres"), null=False)
    apellidos = models.CharField(max_length=100, verbose_name=_("Apellidos"), null=False)
    telefono_legalizacion = models.CharField(max_length=10, verbose_name=_("Teléfono Legalización"), null=False)
    plan_adquiere = models.ForeignKey(Planes_portabilidad, on_delete=models.PROTECT, related_name='ventas_portabilidad', verbose_name=_("Plan Adquirido"), null=False)
    numero_a_portar = models.CharField(max_length=10, verbose_name=_("Número a Portar"), null=False)
    nip = models.IntegerField(verbose_name=_("NIP"), null=False, blank=False)
    fecha_entrega = models.DateField(verbose_name=_("Fecha de Entrega"), null=False, blank=False)
    fecha_ventana_cambio = models.DateField(verbose_name=_("Fecha de Ventana de Cambio"), null=False, blank=False)
    numero_orden = models.IntegerField(verbose_name=_("Número de Orden"), null=False)
    base_origen = models.CharField(max_length=100, verbose_name=_("Base Origen"), null=False)
    usuario_greta = models.CharField(max_length=100, verbose_name=_("Usuario Greta"), null=False)
    confronta = models.FileField(upload_to='confrontas/', verbose_name=_("Confronta"), null=True, blank=True)
    observacion = models.TextField(verbose_name=_("Observación"), null=True, blank=True)
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_portabilidad_realizadas", verbose_name=_("Agente"))
    backoffice = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_portabilidad_revisadas", verbose_name=_("Backoffice"))

    estado_venta = models.CharField(max_length=30, choices=ESTADO_VENTA_CHOICES, default='pendiente_revision', verbose_name=_("Estado Venta"))
    estado_logistica = models.CharField(max_length=21, choices=ESTADO_LOGISTICA_CHOICES, default='pendiente_seguimiento', verbose_name=_("Estado Logística"))
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Venta Portabilidad")
        verbose_name_plural = _("Ventas Portabilidad")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Venta {self.id} - {self.nombres} {self.apellidos} - {self.plan_adquiere}"
    
    def save(self, *args, **kwargs):
        # Si es una nueva venta, generar un número único
        if not self.numero:
            now = timezone.now()
            self.numero = f"PORTA-{now.strftime('%Y%m%d%H%M%S')}"
            
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo_portabilidad(self):
        return f"{self.nombres} {self.apellidos}"


class VentaPrePos(models.Model):

    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'CC'),
        ('CE', 'CE'),
        ('NIT', 'NIT'),
        ('PP', 'Pasaporte'),
    ]

    numero = models.CharField(verbose_name=_("Número"), null=False, blank=False)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, verbose_name=_("Tipo de Cliente"))

    tipo_documento = models.CharField(
        max_length=10, 
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC',
        verbose_name=_("Tipo de Documento")
    )

    documento = models.CharField(max_length=15, verbose_name=_("Documento"), null=False)
    fecha_expedicion = models.DateField(verbose_name=_("Fecha de Expedición"), null=False)
    nombres = models.CharField(max_length=100, verbose_name=_("Nombres"), null=False)
    apellidos = models.CharField(max_length=100, verbose_name=_("Apellidos"), null=False)
    telefono_legalizacion = models.CharField(max_length=10, verbose_name=_("Teléfono Legalización"), null=False)
    plan_adquiere = models.ForeignKey(Planes_portabilidad, on_delete=models.PROTECT, related_name='ventas_prepos', verbose_name=_("Plan Adquirido"), null=False)
    numero_orden = models.IntegerField(verbose_name=_("Número de Orden"), null=False)
    base_origen = models.CharField(max_length=100, verbose_name=_("Base Origen"), null=True, blank=True)
    usuario_greta = models.CharField(max_length=100, verbose_name=_("Usuario Greta"), null=True, blank=True)
    observacion = models.TextField(verbose_name=_("Observación"), null=True, blank=True)
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_prepos_realizadas", verbose_name=_("Agente"))

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Venta PrePos")
        verbose_name_plural = _("Ventas PrePos") 
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Venta {self.id} - {self.nombres} {self.apellidos} - {self.plan_adquiere}"
    
    def save(self, *args, **kwargs):
        # Si es una nueva venta, generar un número único
        if not self.numero:
            now = timezone.now()
            self.numero = f"PREPOS-{now.strftime('%Y%m%d%H%M%S')}"
            
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo_prepos(self):
        return f"{self.nombres} {self.apellidos}"

class VentaUpgrade(models.Model):

    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'CC'),
        ('CE', 'CE'),
        ('NIT', 'NIT'),
        ('PP', 'Pasaporte'),
    ]

    numero = models.CharField(verbose_name=_("Número"), null=False, blank=False)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, verbose_name=_("Tipo de Cliente"))

    tipo_documento = models.CharField(
        max_length=10, 
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC',
        verbose_name=_("Tipo de Documento")
    )

    documento = models.CharField(max_length=15, verbose_name=_("Documento"), null=False)
    fecha_expedicion = models.DateField(verbose_name=_("Fecha de Expedición"), null=False)
    nombres = models.CharField(max_length=100, verbose_name=_("Nombres"), null=False)
    apellidos = models.CharField(max_length=100, verbose_name=_("Apellidos"), null=False)
    telefono_legalizacion = models.CharField(max_length=10, verbose_name=_("Teléfono Legalización"), null=False)
    codigo_verificacion = models.CharField(max_length=6, verbose_name=_("Código de Verificación"), null=False, blank=False)
    plan_adquiere = models.ForeignKey(Planes_portabilidad, on_delete=models.PROTECT, related_name='ventas_upgrade', verbose_name=_("Plan Adquirido"), null=False)
    numero_orden = models.IntegerField(verbose_name=_("Número de Orden"), null=False)
    base_origen = models.CharField(max_length=100, verbose_name=_("Base Origen"), null=False)
    usuario_greta = models.CharField(max_length=100, verbose_name=_("Usuario Greta"), null=False)
    
    observacion = models.TextField(verbose_name=_("Observación"), null=True, blank=True)
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas_upgrade_realizadas", verbose_name=_("Agente"))

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Venta Upgrade")
        verbose_name_plural = _("Ventas Upgrade") 
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Venta {self.id} - {self.nombres} {self.apellidos} - {self.plan_adquiere}"
    
    def save(self, *args, **kwargs):
        # Si es una nueva venta, generar un número único
        if not self.numero:
            now = timezone.now()
            self.numero = f"UPGRADE-{now.strftime('%Y%m%d%H%M%S')}"
            
        super().save(*args, **kwargs)
    
    @property
    def nombre_completo_upgrade(self):
        return f"{self.nombres} {self.apellidos}"

class Agendamiento(models.Model):

    Estado_agendamiento = models.CharField(max_length=20, choices=ESTADO_AGENDAMIENTO_CHOICES, default='agendado', verbose_name=_("Estado"))
    nombre_cliente = models.CharField(max_length=100, verbose_name=_("Nombre del Cliente"))
    telefono_contacto = models.CharField(max_length=15, verbose_name=_("Teléfono de Contacto"))
    fecha_volver_a_llamar = models.DateField(verbose_name=_("Fecha de Volver a Llamar"))
    hora_volver_a_llamar = models.TimeField(verbose_name=_("Hora de Volver a Llamar"))
    observaciones = models.TextField(verbose_name=_("Observaciones"))
    agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agendamientos", verbose_name=_("Agente"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))

    class Meta:
        verbose_name = _("Agendamiento")
        verbose_name_plural = _("Agendamientos")
        ordering = ['-fecha_volver_a_llamar']
    
    def __str__(self):
        return f"Agendamiento {self.id} - {self.nombre_cliente} - {self.fecha_volver_a_llamar}"


class GestionAsesor(models.Model):
    """Modelo para registrar las gestiones realizadas por asesores en las ventas"""
    venta = models.ForeignKey(VentaPortabilidad, on_delete=models.CASCADE, related_name="gestiones_asesor", verbose_name=_("Venta"))
    agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gestiones", verbose_name=_("Agente"))
    comentario = models.TextField(verbose_name=_("Comentario"))
    fecha_gestion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Gestión"))
    
    class Meta:
        verbose_name = _("Gestión Asesor")
        verbose_name_plural = _("Gestiones Asesores")
        ordering = ['-fecha_gestion']
    
    def __str__(self):
        return f"Gestión {self.id} - {self.venta} - {self.fecha_gestion}"


class GestionBackoffice(models.Model):
    """Modelo para registrar las gestiones realizadas por backoffice en las ventas"""
    venta = models.ForeignKey(VentaPortabilidad, on_delete=models.CASCADE, related_name="gestiones_backoffice", verbose_name=_("Venta"))
    backoffice = models.ForeignKey(User, on_delete=models.CASCADE, related_name="validaciones", verbose_name=_("Backoffice"))
    comentario = models.TextField(verbose_name=_("Comentario"))
    fecha_gestion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Gestión"))
    
    class Meta:
        verbose_name = _("Gestión Backoffice")
        verbose_name_plural = _("Gestiones Backoffice")
        ordering = ['-fecha_gestion']
    
    def __str__(self):
        return f"Gestión {self.id} - {self.venta} - {self.fecha_gestion}"


class Escalamiento(models.Model):
    """Modelo para registrar los escalamientos de ventas"""
    TIPO_ESCALAMIENTO_CHOICES = [
        ('documentacion', 'Documentación'),
        ('sistema', 'Sistema'),
        ('otro', 'Otro'),
    ]
    
    venta = models.ForeignKey(VentaPortabilidad, on_delete=models.CASCADE, related_name="escalamientos", verbose_name=_("Venta"))
    tipo_escalamiento = models.CharField(max_length=20, choices=TIPO_ESCALAMIENTO_CHOICES, verbose_name=_("Tipo de Escalamiento"))
    descripcion = models.TextField(verbose_name=_("Descripción"))
    fecha_escalamiento = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Escalamiento"))
    fecha_solucion = models.DateTimeField(null=True, blank=True, verbose_name=_("Fecha de Solución"))
    solucionado = models.BooleanField(default=False, verbose_name=_("Solucionado"))
    
    class Meta:
        verbose_name = _("Escalamiento")
        verbose_name_plural = _("Escalamientos")
        ordering = ['-fecha_escalamiento']
    
    def __str__(self):
        return f"Escalamiento {self.id} - {self.venta} - {self.tipo_escalamiento}"


class Comision(models.Model):
    """Modelo para registrar las comisiones por ventas"""
    ESTADO_COMISION_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('rechazada', 'Rechazada'),
    ]
    
    venta = models.ForeignKey(VentaPortabilidad, on_delete=models.CASCADE, related_name="comisiones", verbose_name=_("Venta"))
    agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comisiones", verbose_name=_("Agente"))
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name=_("Monto"))
    estado = models.CharField(max_length=20, choices=ESTADO_COMISION_CHOICES, default='pendiente', verbose_name=_("Estado"))
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name=_("Fecha de Creación"))
    fecha_pago = models.DateField(null=True, blank=True, verbose_name=_("Fecha de Pago"))
    
    class Meta:
        verbose_name = _("Comisión")
        verbose_name_plural = _("Comisiones")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Comisión {self.id} - {self.venta} - {self.monto}"
