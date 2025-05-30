from django.db import models

ESTADO_CONTACTO_CHOICES = [
    ('contacto_efectivo', 'Contacto Efectivo'),
    ('contacto_no_efectivo', 'Contacto No Efectivo'),
    ('contacto_fallido', 'Contacto Fallido'),
]

GESTION_OPCIONES = {
    'contacto_efectivo': {
        'label': 'Contacto Efectivo',
        'nivel1': {
            'deudor': {
                'label': 'Deudor',
                'nivel2': {
                    'AP': 'AP- Acuerdo de pago formalizado',
                    'PP': 'PP - Promesa de pago',
                    'NC': 'NC -Negociación en curso / pendiente de validación',
                    'RN': 'RN - Rechaza negociación',
                    'ND': 'ND - Niega deuda',
                    'REMITE_ABOGADO': 'Remite a abogado',
                    'SOLICITA_INFO': 'Solicita más información',
                    'SOLICITA_LLAMADA': 'Solicita llamada posterior',
                    'NO_CAPACIDAD_PAGO': 'No tiene capacidad de pago',
                    'TRAMITE_RECLAMO': 'Trámite de reclamo en curso',
                    'PAGADO': 'PAGADO',
                }
            },
            'tercero': {
                'label': 'Tercero',
                'nivel2': {
                    'AP': 'AP- Acuerdo de pago formalizado',
                    'PP': 'PP - Promesa de pago',
                    'NC': 'NC -Negociación en curso / pendiente de validación',
                    'RN': 'RN - Rechaza negociación',
                    'ND': 'ND - Niega deuda',
                    'REMITE_ABOGADO': 'Remite a abogado',
                    'SOLICITA_INFO': 'Solicita más información',
                    'SOLICITA_LLAMADA': 'Solicita llamada posterior',
                    'NO_CAPACIDAD_PAGO': 'No tiene capacidad de pago',
                    'TRAMITE_RECLAMO': 'Trámite de reclamo en curso',
                    'PAGADO': 'PAGADO',
                }
            }
        }
    },
    'contacto_no_efectivo': {
        'label': 'Contacto No Efectivo',
        'nivel1': {
            'telefono_apagado': {
                'label': 'Teléfono apagado / fuera de servicio',
                'nivel2': {'MENSAJE_VOZ': 'Se deja mensaje de voz'}
            },
            'no_contesta': {
                'label': 'No contesta',
                'nivel2': {'MENSAJE_VOZ': 'Se deja mensaje de voz'}
            },
            'buzon_voz': {
                'label': 'Buzón de voz',
                'nivel2': {'MENSAJE_VOZ': 'Se deja mensaje de voz'}
            }
        }
    },
    'contacto_fallido': {
        'label': 'Contacto Fallido',
        'nivel1': {
            'numero_equivocado': {'label': 'Número equivocado', 'nivel2': {'NA': 'N/A'}},
            'numero_inexistente': {'label': 'Número inexistente', 'nivel2': {'NA': 'N/A'}}
        }
    }
}
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class LoginUser(models.Model):
    created_user = models.DateTimeField(auto_now_add=True)
    id_user = models.CharField(max_length=10)
    tipo = models.CharField(max_length=10)
    ip = models.CharField(max_length=20, null=True, blank=True)

    @classmethod
    def registrar(cls, user, tipo, ip=None):
        return cls.objects.create(id_user=str(user.id), tipo=tipo, ip=ip)

    class Meta:
        db_table = 'login_user'

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
    TIPO_GESTION_N1_OPCIONES = {
        CONTACTO_EFECTIVO: [
            ('deudor', 'Deudor'),
            ('tercero', 'Tercero')
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
    
    # Opciones nivel 2 para cada opción de nivel 1
    TIPO_GESTION_N2_OPCIONES = {
        'deudor': [
            ('ap', 'AP - Acuerdo de pago formalizado'),
            ('pp', 'PP - Promesa de pago'),
            ('nc', 'NC - Negociación en curso / pendiente de validación'),
            ('rn', 'RN - Rechaza negociación'),
            ('nd', 'ND - Niega deuda'),
            ('abogado', 'Remite a abogado'),
            ('solicita_info', 'Solicita más información'),
            ('solicita_llamada', 'Solicita llamada posterior'),
            ('no_capacidad', 'No tiene capacidad de pago'),
            ('reclamo', 'Trámite de reclamo en curso'),
            ('pagado', 'PAGADO')
        ],
        'tercero': [
            ('informacion', 'Brinda información'),
            ('no_informacion', 'No brinda información')
        ],
        'buzon_voz': [
            ('mensaje_voz', 'Se deja mensaje de voz')
        ]
    }

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='gestiones')
    usuario_gestion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='gestiones_realizadas')
    fecha_hora_gestion = models.DateTimeField(default=timezone.now)

    canal_contacto = models.CharField(max_length=50, choices=CANAL_CONTACTO_CHOICES)
    estado_contacto = models.CharField(max_length=50, choices=ESTADO_CONTACTO_CHOICES)

    tipo_gestion_n1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Gestión (Nivel 1)")
    tipo_gestion_n2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Gestión (Nivel 2)")
    tipo_gestion_n3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Gestión (Nivel 3)")

    acuerdo_pago_realizado = models.BooleanField(default=False, verbose_name="¿Se realizó acuerdo de pago?")
    fecha_acuerdo = models.DateField(blank=True, null=True, verbose_name="Fecha de Acuerdo")
    monto_acuerdo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Monto del Acuerdo")
    observaciones_acuerdo = models.TextField(blank=True, null=True, verbose_name="Observaciones del Acuerdo")

    seguimiento_requerido = models.BooleanField(default=False, verbose_name="¿Requiere seguimiento?")
    fecha_proximo_seguimiento = models.DateField(blank=True, null=True, verbose_name="Fecha Próximo Seguimiento")
    hora_proximo_seguimiento = models.TimeField(blank=True, null=True, verbose_name="Hora Próximo Seguimiento")

    observaciones_generales = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales de la Gestión")
    
    # Campos para comprobante de pago
    comprobante_pago = models.FileField(upload_to='comprobantes_pago/', blank=True, null=True, verbose_name="Comprobante de Pago")
    fecha_pago_efectivo = models.DateField(blank=True, null=True, verbose_name="Fecha de Pago Efectivo")

    class Meta:
        verbose_name = "Gestión"
        verbose_name_plural = "Gestiones"
        ordering = ['-fecha_hora_gestion']

    def __str__(self):
        return f"Gestión para {self.cliente.nombre_completo} el {self.fecha_hora_gestion.strftime('%Y-%m-%d %H:%M')}"
