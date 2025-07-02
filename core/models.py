from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

ESTADO_CONTACTO_CHOICES = [
    ('contacto_efectivo', 'Contacto Efectivo'),
    ('contacto_no_efectivo', 'Contacto No Efectivo'),
    ('contacto_fallido', 'Contacto Fallido'),
]

GESTION_OPCIONES = {
    'contacto_efectivo': {
        'label': 'Contacto Efectivo',
        'nivel1': {
            'AP': {'label': 'AP - Acuerdo de pago formalizado'},
            'SAP': {'label': 'SAP - Seguimiento Acuerdo de pago'},
            'NC': {'label': 'NC - Negociación en curso'},
            'PV': {'label': 'PV - Pendiente de validación'},
            'RN': {'label': 'RN - Rechaza negociación'},
            'ND': {'label': 'ND - Niega deuda'},
            'CLIENTE_CUELGA': {'label': 'Cliente cuelga'},
            'REMITE_ABOGADO': {'label': 'Remite a abogado'},
            'SOLICITA_INFO': {'label': 'Solicita más información'},
            'SOLICITA_LLAMADA': {'label': 'Solicita llamada posterior'},
            'NO_CAPACIDAD_PAGO': {'label': 'No tiene capacidad de pago'},
            'TITULAR_FALLECIDO': {'label': 'Titular fallecido'},
            'TRAMITE_RECLAMO': {'label': 'Trámite de reclamo en curso'},
            'TERCERO_INFORMACION': {'label': 'Tercero brinda información'},
            'TERCERO_NO_INFORMACION': {'label': 'Tercero no brinda información'},
            'SIN_RESPUESTA_WP': {'label': 'Sin respuesta en WhatsApp'},
            'SALDADO_LINERU': {'label': 'Saldado con LINERU'}
        }
    },  
    'contacto_no_efectivo': {
        'label': 'Contacto No Efectivo',
        'nivel1': {
            'ASEGURA QUE PAGO': {'label': 'Asegura que pago'},
            'TELEFONO_APAGADO': {'label': 'Teléfono apagado'},
            'FUERA_DE_SERVICIO': {'label': 'Fuera de servicio'},
            'NO_CONTESTA': {'label': 'No contesta'},
            'BUZON_VOZ': {'label': 'Buzón de voz'},
        }
    },
    'contacto_fallido': {
        'label': 'Contacto Fallido',
        'nivel1': {
            'NUMERO_EQUIVOCADO': {'label': 'Número equivocado'},
            'NUMERO_INEXISTENTE': {'label': 'Número inexistente'}
        }
    }
}


# La definición antigua del modelo LoginUser se ha eliminado para evitar duplicidades.
# Ahora se utiliza la versión actualizada que se encuentra más adelante en este archivo.


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre_empleado = models.CharField(max_length=50, null=True, blank=True)
    apellido_empleado = models.CharField(max_length=50, null=True, blank=True)
    sexo_empleado = models.IntegerField(null=True, blank=True)
    telefono_empleado = models.CharField(max_length=50, null=True, blank=True)
    email_empleado = models.CharField(max_length=50, null=True, blank=True)
    profesion_empleado = models.CharField(max_length=50, null=True, blank=True)
    foto_empleado = models.TextField(null=True, blank=True)
    salario_empleado = models.BigIntegerField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    documento = models.BigIntegerField()

    class Meta:
        db_table = 'tbl_empleados'


class Cliente(models.Model):
    CEDULA_CIUDADANIA = 'CC'
    CEDULA_EXTRANJERIA = 'CE'
    TARJETA_IDENTIDAD = 'TI'
    NIT = 'NIT'
    PASAPORTE = 'PAS'
    OPCIONES_TIPO_DOCUMENTO = [
        (CEDULA_CIUDADANIA, 'CC'),
        (CEDULA_EXTRANJERIA, 'CE'),
        (TARJETA_IDENTIDAD, 'TI'), 
        (NIT, 'NIT'),
        (PASAPORTE, 'PAS'),
    ]

    ACTIVO = 'Activo'
    INACTIVO = 'Inactivo'
    OPCIONES_ESTADO = [
        (ACTIVO, 'Activo'),
        (INACTIVO, 'Inactivo'),
    ]

    fecha_act = models.DateField(null=True, blank=True)
    documento = models.CharField(max_length=30)
    referencia = models.CharField(max_length=50, blank=True, null=True)
    tipo_documento = models.CharField(
        max_length=30, 
        choices=OPCIONES_TIPO_DOCUMENTO, 
        blank=True, 
        null=True
    ) 
    
    nombre_completo = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    dias_mora_originador = models.FloatField(default=0, null=True, blank=True) 
    dias_mora_caso_sas = models.FloatField(default=0, null=True, blank=True)
    total_dias_mora = models.FloatField(default=0, null=True, blank=True)
    anios_mora = models.FloatField(default=0, null=True, blank=True)
    principal = models.DecimalField(max_digits=16, decimal_places=2, default=0) 
    deuda_principal_k = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    intereses = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    tecnologia = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    seguro = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    otros_cargos = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    total_pagado = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    dcto_pago_contado_50 = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    dcto_pago_contado_70_max_30 = models.DecimalField(max_digits=16, decimal_places=2, default=0, null=True, blank=True)
    deuda_total = models.DecimalField(max_digits=16, decimal_places=2, default=0) 
    fecha_cesion = models.DateField(blank=True, null=True) 
    telefono_celular = models.CharField(max_length=20, blank=True, null=True) 
    email = models.EmailField(blank=True, null=True)
    celular_1 = models.CharField(max_length=20, default='') 
    celular_2 = models.CharField(max_length=20, blank=True, null=True)
    celular_3 = models.CharField(max_length=20, blank=True, null=True)
    direccion_1 = models.CharField(max_length=255, blank=True, null=True)
    direccion_2 = models.CharField(max_length=255, blank=True, null=True)
    direccion_3 = models.CharField(max_length=255, blank=True, null=True)
    email_1 = models.CharField(max_length=100, blank=True, null=True) 
    email_2 = models.CharField(max_length=100, blank=True, null=True)
    telefono_1 = models.CharField(max_length=20, blank=True, null=True)
    telefono_2 = models.CharField(max_length=20, blank=True, null=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) 
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, 
        choices=OPCIONES_ESTADO, 
        default=ACTIVO
    ) 
    observaciones_adicionales = models.TextField(blank=True, null=True) 
    tipo_cliente = models.CharField(max_length=50, blank=True, null=True) 

    class Meta:
        db_table = "clientes"
        unique_together = (('documento', 'referencia'),)
        # verbose_name = "Cliente" 
        # verbose_name_plural = "Clientes" 

    def calcular_dias_mora_actual(self):
        """Calcula los días de mora actuales basados en la fecha actual y la fecha de cesión"""
        from django.utils import timezone
        import datetime
        
        if not self.fecha_cesion:
            return self.dias_mora_originador or 0
            
        fecha_actual = timezone.localdate()
        dias_adicionales = (fecha_actual - self.fecha_cesion).days
        
        # Sumamos los días de mora del originador con los días transcurridos desde la cesión
        dias_mora_total = (self.dias_mora_originador or 0) + dias_adicionales
        
        return dias_mora_total
    
    def __str__(self):
        return self.nombre_completo if self.nombre_completo else str(self.id)


class Gestion(models.Model):
    # Opciones de canal de contacto
    CANAL_CONTACTO_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telefono_in', 'Teléfono IN'),
        ('telefono_out', 'Teléfono OUT'),
        ('email', 'Email'),
        ('sms', 'SMS')
    ]
    
    # Estados de contacto principales (Nivel 1)
    CONTACTO_EFECTIVO = 'contacto_efectivo'
    CONTACTO_NO_EFECTIVO = 'contacto_no_efectivo'
    CONTACTO_FALLIDO = 'contacto_fallido'
    
    ESTADO_CONTACTO_CHOICES = [
        (CONTACTO_EFECTIVO, 'Contacto Efectivo'),
        (CONTACTO_NO_EFECTIVO, 'Contacto No Efectivo'),
        (CONTACTO_FALLIDO, 'Contacto Fallido'),
    ]
    
    # Opciones nivel 1 para cada estado de contacto
    # Nota: 
    # - 'ap' en contacto_efectivo marcan automáticamente acuerdo_pago_realizado = True
    # - 'solicita_llamada' marca automáticamente seguimiento_requerido = True
    TIPO_GESTION_N1_OPCIONES = {
        CONTACTO_EFECTIVO: [
            ('ap', 'AP - Acuerdo de pago formalizado'),
            ('sap', 'SAP - Seguimiento Acuerdo de pago'),
            ('nc', 'NC - Negociación en curso / pendiente de validación'),
            ('rn', 'RN - Rechaza negociación'),
            ('nd', 'ND - Niega deuda'),
            ('abogado', 'Remite a abogado'),
            ('solicita_info', 'Solicita más información'),
            ('solicita_llamada', 'Solicita llamada posterior'),
            ('no_capacidad', 'No tiene capacidad de pago'),
            ('reclamo', 'Trámite de reclamo en curso'),
            ('tercero_informacion', 'Tercero brinda información'),
            ('tercero_no_informacion', 'Tercero no brinda información'),
            ('sin_respuesta_wp', 'Sin respuesta en WhatsApp'),
            ('saldado_lineru', 'Saldado con LINERU')  
        ],
        CONTACTO_NO_EFECTIVO: [
            ('telefono_apagado', 'Teléfono apagado / fuera de servicio'),
            ('no_contesta', 'No contesta'),
            ('buzon_voz', 'Buzón de voz')
        ],
        CONTACTO_FALLIDO: [
            ('numero_equivocado', 'Número equivocado'),
            ('numero_inexistente', 'Número inexistente')
        ]
    }
    

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='gestiones')
    usuario_gestion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='gestiones_realizadas')
    fecha_hora_gestion = models.DateTimeField(default=timezone.now)

    canal_contacto = models.CharField(max_length=50, choices=CANAL_CONTACTO_CHOICES)
    estado_contacto = models.CharField(max_length=50, choices=ESTADO_CONTACTO_CHOICES)

    tipo_gestion_n1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Gestión (Nivel 1)")

    referencia_producto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia de Producto")
    acuerdo_pago_realizado = models.BooleanField(default=False, verbose_name="¿Se realizó acuerdo de pago?")
    fecha_acuerdo = models.DateField(blank=True, null=True, verbose_name="Fecha de Acuerdo")
    monto_acuerdo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Monto del Acuerdo")
    observaciones_acuerdo = models.TextField(blank=True, null=True, verbose_name="Observaciones del Acuerdo")

    seguimiento_requerido = models.BooleanField(default=False, verbose_name="¿Requiere seguimiento?")
    fecha_proximo_seguimiento = models.DateField(blank=True, null=True, verbose_name="Fecha Próximo Seguimiento")
    hora_proximo_seguimiento = models.TimeField(blank=True, null=True, verbose_name="Hora Próximo Seguimiento")
    seguimiento_completado = models.BooleanField(default=False, verbose_name="Seguimiento completado")

    observaciones_generales = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales de la Gestión")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    # Campos para comprobante de pago
    comprobante_pago = models.FileField(upload_to='comprobantes_pago/', blank=True, null=True, verbose_name="Comprobante de Pago")
    fecha_pago_efectivo = models.DateField(blank=True, null=True, verbose_name="Fecha de Pago Efectivo")

    class Meta:
        verbose_name = "Gestión"
        verbose_name_plural = "Gestiones"
        ordering = ['-fecha_hora_gestion']

    def save(self, *args, **kwargs):
        # Si el tipo de gestión es AP o PP, marcar automáticamente como acuerdo de pago
        if self.tipo_gestion_n1 in ['ap']:
            self.acuerdo_pago_realizado = True
            
        # Si el tipo de gestión es solicita_llamada, marcar como requiere seguimiento
        if self.tipo_gestion_n1 == 'solicita_llamada':
            self.seguimiento_requerido = True
        
        # Continuar con el guardado normal
        super(Gestion, self).save(*args, **kwargs)
        
        # NOTA: La creación del acuerdo de pago ahora se maneja en la vista detalle_cliente
        # para evitar duplicación de lógica y tener un mejor control sobre el proceso
    
    def __str__(self):
        return f"Gestión para {self.cliente.nombre_completo} el {self.fecha_hora_gestion.strftime('%Y-%m-%d %H:%M')}"


class AcuerdoPago(models.Model):
    # Estados posibles del acuerdo
    PENDIENTE = 'pendiente'
    EN_CURSO = 'en_curso'
    COMPLETADO = 'completado'
    INCUMPLIDO = 'incumplido'
    CANCELADO = 'cancelado'
    
    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (EN_CURSO, 'En curso'),
        (COMPLETADO, 'Completado'),
        (INCUMPLIDO, 'Incumplido'),
        (CANCELADO, 'Cancelado'),
    ]
    
    # Tipos de acuerdo
    PAGO_TOTAL = 'pago_total'
    PAGO_PARCIAL = 'pago_parcial'
    
    TIPO_ACUERDO_CHOICES = [
        (PAGO_TOTAL, 'Pago total'),
        (PAGO_PARCIAL, 'Pago parcial'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='acuerdos_pago')
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE, related_name='acuerdos')
    referencia_producto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia de Producto")
    fecha_acuerdo = models.DateField(verbose_name="Fecha de creación del acuerdo")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto total del acuerdo")
    numero_cuotas = models.PositiveIntegerField(default=1, verbose_name="Número de cuotas")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=PENDIENTE, verbose_name="Estado del acuerdo")
    tipo_acuerdo = models.CharField(max_length=20, choices=TIPO_ACUERDO_CHOICES, default=PAGO_TOTAL, verbose_name="Tipo de acuerdo")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='acuerdos_creados')
    
    class Meta:
        verbose_name = "Acuerdo de pago"
        verbose_name_plural = "Acuerdos de pago"
        ordering = ['-fecha_acuerdo']
    
    def __str__(self):
        return f"Acuerdo de {self.cliente.nombre_completo} por ${self.monto_total:,} del {self.fecha_acuerdo}"
    
    def actualizar_estado(self):
        """Actualiza el estado del acuerdo basado en el estado de sus cuotas"""
        cuotas = self.cuotas.all()
        total_cuotas = cuotas.count()
        
        if total_cuotas == 0:
            self.estado = self.PENDIENTE
            self.save()
            return
            
        cuotas_pagadas = cuotas.filter(estado='pagada').count()
        cuotas_vencidas = cuotas.filter(fecha_vencimiento__lt=timezone.now().date(), estado='pendiente').count()
        
        if cuotas_pagadas == total_cuotas:
            self.estado = self.COMPLETADO
        elif cuotas_vencidas > 0:
            self.estado = self.INCUMPLIDO
        elif cuotas_pagadas > 0:
            self.estado = self.EN_CURSO
        else:
            self.estado = self.PENDIENTE
            
        self.save()


class CuotaAcuerdo(models.Model):
    # Estados posibles de la cuota
    PENDIENTE = 'pendiente'
    PAGADA = 'pagada'
    VENCIDA = 'vencida'
    
    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (PAGADA, 'Pagada'),
        (VENCIDA, 'Vencida'),
    ]
    
    acuerdo = models.ForeignKey(AcuerdoPago, on_delete=models.CASCADE, related_name='cuotas')
    numero_cuota = models.PositiveIntegerField(verbose_name="Número de cuota")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto de la cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de pago efectivo")
    comprobante_pago = models.FileField(upload_to='comprobantes_cuotas/', null=True, blank=True, verbose_name="Comprobante de pago")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=PENDIENTE, verbose_name="Estado de la cuota")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Cuota de acuerdo"
        verbose_name_plural = "Cuotas de acuerdos"
        ordering = ['acuerdo', 'numero_cuota']
        unique_together = ['acuerdo', 'numero_cuota']
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} de acuerdo {self.acuerdo.id} - ${self.monto:,}"
    
    def save(self, *args, **kwargs):
        # Si se marca como pagada y no tiene fecha de pago, establecer fecha actual
        if self.estado == self.PAGADA and not self.fecha_pago:
            self.fecha_pago = timezone.now().date()
        
        # Si está pendiente y la fecha de vencimiento ya pasó, marcar como vencida
        if self.estado == self.PENDIENTE and self.fecha_vencimiento < timezone.now().date():
            self.estado = self.VENCIDA
            
        super().save(*args, **kwargs)
        
        # Actualizar el estado del acuerdo padre
        self.acuerdo.actualizar_estado()


class LoginUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="logins")
    tipo = models.CharField(max_length=50, default="login")
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Login de usuario"
        verbose_name_plural = "Logins de usuario"
        ordering = ["-fecha"]
    
    @classmethod
    def registrar(cls, user, tipo="login", ip=None):
        return cls.objects.create(user=user, tipo=tipo, ip=ip)


class Campana(models.Model):
    """Modelo para gestionar las diferentes campañas en el sistema."""
    nombre = models.CharField(max_length=100, verbose_name=_('Nombre'))
    codigo = models.CharField(max_length=50, unique=True, verbose_name=_('Código'))
    descripcion = models.TextField(blank=True, null=True, verbose_name=_('Descripción'))
    activa = models.BooleanField(default=True, verbose_name=_('Activa'))
    modulo = models.CharField(
        max_length=50, 
        choices=[('core', 'Core'), ('telefonica', 'Telefónica')],
        default='core',
        verbose_name=_('Módulo')
    )
    usuarios = models.ManyToManyField(User, blank=True, related_name='campanas', verbose_name=_('Usuarios'))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    
    class Meta:
        verbose_name = _('Campaña')
        verbose_name_plural = _('Campañas')
        ordering = ['nombre']
        
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
