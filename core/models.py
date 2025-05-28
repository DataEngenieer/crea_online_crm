from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

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

    fecha_cesion = models.DateField(null=True, blank=True)
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
