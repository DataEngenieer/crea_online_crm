from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import string
import random


# Opciones para estados de ventas de tarjeta plata
ESTADO_VENTA_TARJETA_CHOICES = [
    ('nueva', 'Nueva'),
    ('aceptada', 'Aceptada'),
    ('rechazada', 'Rechazada'),
]

# Opciones para factibilidad
FACTIBILIDAD_CHOICES = [
    ('alta', 'Alta'),
    ('media', 'Media'),
    ('baja', 'Baja'),
]

# Opciones para tipo de cliente
TIPO_CLIENTE_CHOICES = [
    ('nuevo', 'Nuevo'),
    ('existente', 'Existente'),
]

# Opciones para género
GENERO_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro'),
]

# Opciones para Call Review
CALL_REVIEW_CHOICES = [
    ('si', 'Sí'),
    ('no', 'No'),
]

# Opciones para tipo de entrega
ENTREGA_CHOICES = [
    ('domicilio', 'Domicilio'),
    ('centro_comercial', 'Centro Comercial'),
]

# Opciones para resultado de venta
RESULTADO_CHOICES = [
    ('venta_bbd', 'Venta BBD'),
    ('venta_referidos', 'Venta Referidos'),
    ('rechazada', 'Rechazada'),
    ('venta_md', 'Venta MD'),
    ('otro', 'Otro'),
]


class ClienteTarjetaPlata(models.Model):
    """Modelo para almacenar los clientes potenciales de tarjeta de crédito mexicanos"""
    
    item = models.CharField(max_length=50, unique=True, verbose_name=_("Item"))
    telefono = models.CharField(max_length=20, verbose_name=_("Teléfono"))
    nombre_completo = models.CharField(max_length=200, verbose_name=_("Nombre Completo"))
    factibilidad = models.CharField(
        max_length=10, 
        choices=FACTIBILIDAD_CHOICES, 
        verbose_name=_("Factibilidad")
    )
    tipo = models.CharField(
        max_length=15, 
        choices=TIPO_CLIENTE_CHOICES, 
        verbose_name=_("Tipo")
    )
    rfc = models.CharField(max_length=13, verbose_name=_("RFC"))
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Nacimiento")
    )
    genero = models.CharField(
        max_length=1, 
        choices=GENERO_CHOICES, 
        verbose_name=_("Género")
    )
    email = models.EmailField(verbose_name=_("Email"))
    
    # Campos de control
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Cliente Tarjeta Plata")
        verbose_name_plural = _("Clientes Tarjeta Plata")
        ordering = ['-fecha_creacion']
    
    def save(self, *args, **kwargs):
        if not self.item:
            self.item = self.generar_id_unico()
        super().save(*args, **kwargs)
    
    def generar_id_unico(self):
        """Genera un ID único para el cliente"""
        import uuid
        return f"CL-{uuid.uuid4().hex[:8].upper()}"
    
    @property
    def edad(self):
        """Calcula la edad del cliente basada en su fecha de nacimiento"""
        if self.fecha_nacimiento:
            from datetime import date
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.telefono}"


class VentaTarjetaPlata(models.Model):
    """Modelo para almacenar las ventas de tarjetas de crédito"""
    
    # Campos principales
    id_preap = models.CharField(
        max_length=5, 
        unique=True, 
        blank=True,
        verbose_name=_("ID PreAp"),
        help_text=_("ID de preaprobación generado automáticamente por el sistema")
    )
    item = models.CharField(max_length=50, verbose_name=_("Item"))
    nombre = models.CharField(max_length=200, verbose_name=_("Nombre"))
    ine = models.CharField(max_length=20, verbose_name=_("INE"))
    rfc = models.CharField(max_length=13, verbose_name=_("RFC"))
    telefono = models.CharField(max_length=20, verbose_name=_("Teléfono"))
    correo = models.EmailField(verbose_name=_("Correo"))
    direccion = models.TextField(verbose_name=_("Dirección"))
    codigo_postal = models.CharField(max_length=10, verbose_name=_("Código Postal"))
    
    # Relación con cliente base (opcional)
    cliente_base = models.ForeignKey(
        ClienteTarjetaPlata, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name=_("Cliente Base")
    )
    
    # Estado de la venta
    estado_venta = models.CharField(
        max_length=20, 
        choices=ESTADO_VENTA_TARJETA_CHOICES, 
        default='nueva', 
        verbose_name=_("Estado Venta")
    )
    
    # Nuevos campos agregados
    usuario_c8 = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Usuario C8")
    )
    entrega = models.CharField(
        max_length=20, 
        choices=ENTREGA_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name=_("Tipo de Entrega")
    )
    dn = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("DN")
    )
    estado_republica = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Estado República")
    )
    ingreso_mensual_cliente = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_("Ingreso Mensual Cliente")
    )
    resultado = models.CharField(
        max_length=20, 
        choices=RESULTADO_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name=_("Resultado")
    )
    
    # Usuarios relacionados
    agente = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="ventas_tarjeta_plata_realizadas", 
        verbose_name=_("Agente")
    )
    backoffice = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="ventas_tarjeta_plata_revisadas", 
        verbose_name=_("Backoffice")
    )
    
    # Campos de control
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    fecha_revision = models.DateTimeField(null=True, blank=True, verbose_name=_("Fecha de Revisión"))
    
    # Observaciones
    observaciones = models.TextField(null=True, blank=True, verbose_name=_("Observaciones"))
    
    class Meta:
        verbose_name = _("Venta Tarjeta Plata")
        verbose_name_plural = _("Ventas Tarjeta Plata")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.id_preap} - {self.nombre}"
    
    def generar_id_preap(self):
        """Genera un ID PreAp único consecutivo alfanumérico de 5 dígitos"""
        # Obtener el último ID PreAp creado ordenado por el campo id_preap para garantizar secuencia
        ultimo_id = VentaTarjetaPlata.objects.filter(
            id_preap__isnull=False
        ).exclude(
            id_preap=''
        ).order_by('-id_preap').first()
        
        if ultimo_id and ultimo_id.id_preap:
            # Extraer la parte numérica del último ID
            try:
                letra = ultimo_id.id_preap[0]
                numero = int(ultimo_id.id_preap[1:])
                
                # Incrementar el número
                numero += 1
                
                # Si el número excede 9999, cambiar a la siguiente letra
                if numero > 9999:
                    # Obtener la siguiente letra del alfabeto
                    siguiente_letra_ord = ord(letra) + 1
                    if siguiente_letra_ord > ord('Z'):
                        siguiente_letra_ord = ord('A')  # Reiniciar en A
                    letra = chr(siguiente_letra_ord)
                    numero = 1
                
                nuevo_id = f"{letra}{numero:04d}"
                
                # Verificar que el ID no exista ya (medida de seguridad adicional)
                contador_intentos = 0
                while VentaTarjetaPlata.objects.filter(id_preap=nuevo_id).exists() and contador_intentos < 100:
                    numero += 1
                    if numero > 9999:
                        siguiente_letra_ord = ord(letra) + 1
                        if siguiente_letra_ord > ord('Z'):
                            siguiente_letra_ord = ord('A')
                        letra = chr(siguiente_letra_ord)
                        numero = 1
                    nuevo_id = f"{letra}{numero:04d}"
                    contador_intentos += 1
                
                return nuevo_id
            except (ValueError, IndexError):
                # Si hay error en el formato, empezar desde A0001
                return "A0001"
        else:
            # Si no hay registros previos, empezar desde A0001
            return "A0001"
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para generar ID automático y actualizar fecha_revision"""
        # Generar ID PreAp automáticamente si no existe
        if not self.id_preap:
            self.id_preap = self.generar_id_preap()
            # El método generar_id_preap() ya maneja la verificación de unicidad internamente
            # No necesitamos un bucle adicional aquí
        
        # Lógica existente para fecha_revision
        if self.pk:
            # Si ya existe, verificar si cambió el estado
            try:
                original = VentaTarjetaPlata.objects.get(pk=self.pk)
                if original.estado_venta != self.estado_venta and self.estado_venta in ['aceptada', 'rechazada']:
                    self.fecha_revision = timezone.now()
            except VentaTarjetaPlata.DoesNotExist:
                # Si por alguna razón no existe el objeto original, continuar sin error
                pass
        
        super().save(*args, **kwargs)


class AuditoriaBackofficeTarjetaPlata(models.Model):
    """Modelo para el seguimiento y auditoría del backoffice"""
    
    def generar_id_auditoria():
        """Genera un ID único para la auditoría"""
        caracteres = string.ascii_uppercase + string.digits
        while True:
            id_auditoria = 'AUD' + ''.join(random.choices(caracteres, k=7))
            if not AuditoriaBackofficeTarjetaPlata.objects.filter(id_auditoria_back=id_auditoria).exists():
                return id_auditoria
    
    id_auditoria_back = models.CharField(
        max_length=50, 
        unique=True, 
        default=generar_id_auditoria, 
        verbose_name=_("ID Auditoría Back")
    )
    
    # Relación con la venta
    venta = models.ForeignKey(
        VentaTarjetaPlata, 
        on_delete=models.CASCADE, 
        related_name="auditorias_backoffice", 
        verbose_name=_("Venta")
    )
    
    # Campos de auditoría
    call_review = models.CharField(
        max_length=2, 
        choices=CALL_REVIEW_CHOICES, 
        verbose_name=_("Call Review")
    )
    call_upload = models.FileField(
        upload_to='tarjeta_plata/call_uploads/', 
        null=True, 
        blank=True, 
        verbose_name=_("Call Upload")
    )
    
    # Usuario que realiza la auditoría
    auditor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="auditorias_tarjeta_plata", 
        verbose_name=_("Auditor")
    )
    
    # Campos adicionales
    observaciones_auditoria = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Observaciones de Auditoría")
    )
    
    # Campos de control
    fecha_auditoria = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Auditoría"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))
    
    class Meta:
        verbose_name = _("Auditoría Backoffice Tarjeta Plata")
        verbose_name_plural = _("Auditorías Backoffice Tarjeta Plata")
        ordering = ['-fecha_auditoria']
    
    def __str__(self):
        return f"{self.id_auditoria_back} - {self.venta.id_preap}"


class GestionBackofficeTarjetaPlata(models.Model):
    """Modelo para registrar las gestiones del backoffice sobre las ventas"""
    
    venta = models.ForeignKey(
        VentaTarjetaPlata, 
        on_delete=models.CASCADE, 
        related_name="gestiones_backoffice", 
        verbose_name=_("Venta")
    )
    backoffice = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="gestiones_tarjeta_plata", 
        verbose_name=_("Backoffice")
    )
    estado_anterior = models.CharField(
        max_length=20, 
        choices=ESTADO_VENTA_TARJETA_CHOICES, 
        verbose_name=_("Estado Anterior")
    )
    estado_nuevo = models.CharField(
        max_length=20, 
        choices=ESTADO_VENTA_TARJETA_CHOICES, 
        verbose_name=_("Estado Nuevo")
    )
    comentario = models.TextField(verbose_name=_("Comentario"))
    archivo_llamada = models.FileField(
        upload_to='tarjeta_plata/llamadas/',
        null=True,
        blank=True,
        verbose_name=_("Archivo de Llamada"),
        help_text=_("Archivo de audio de la llamada de venta (opcional)")
    )
    fecha_gestion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Gestión"))
    
    class Meta:
        verbose_name = _("Gestión Backoffice Tarjeta Plata")
        verbose_name_plural = _("Gestiones Backoffice Tarjeta Plata")
        ordering = ['-fecha_gestion']
    
    def __str__(self):
        return f"{self.venta.id_preap} - {self.estado_anterior} → {self.estado_nuevo}"
