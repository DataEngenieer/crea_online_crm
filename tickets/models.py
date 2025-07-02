from django.db import models
from django.conf import settings
from django.utils import timezone
import os

class Ticket(models.Model):
    """
    Modelo para almacenar las solicitudes de soporte (tickets).
    """
    class Aplicativo(models.TextChoices):
        CARTERA = 'CARTERA', 'Cartera'
        TELEFONICA = 'TELEFONICA', 'Telefónica'
        VICIDIAL = 'VICIDIAL', 'Vicidial'

    class Tipo(models.TextChoices):
        INCONVENIENTE = 'IN', 'Inconveniente'
        REQUERIMIENTO = 'RQ', 'Requerimiento'

    class Estado(models.TextChoices):
        ABIERTO = 'AB', 'Abierto'
        EN_PROGRESO = 'EP', 'En Progreso'
        PENDIENTE = 'PE', 'Pendiente de Tercero'
        RESUELTO = 'RS', 'Resuelto'
        CERRADO = 'CE', 'Cerrado'

    class Prioridad(models.TextChoices):
        BAJA = 'BA', 'Baja'
        MEDIA = 'ME', 'Media'
        ALTA = 'AL', 'Alta'
        URGENTE = 'UR', 'Urgente'

    titulo = models.CharField(max_length=255, help_text="Asunto o título principal del ticket.")
    descripcion = models.TextField(help_text="Descripción detallada del inconveniente o requerimiento.")
    aplicativo = models.CharField(
        max_length=20, 
        choices=Aplicativo.choices, 
        default=Aplicativo.CARTERA,
        verbose_name='Aplicativo',
        help_text='Seleccione el aplicativo relacionado con el ticket'
    )
    tipo = models.CharField(max_length=2, choices=Tipo.choices, default=Tipo.INCONVENIENTE)
    estado = models.CharField(max_length=2, choices=Estado.choices, default=Estado.ABIERTO)
    prioridad = models.CharField(max_length=2, choices=Prioridad.choices, default=Prioridad.MEDIA)
    
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets_solicitados')
    asignado_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True, help_text="Fecha en que se resolvió el ticket.")
    fecha_cierre = models.DateTimeField(null=True, blank=True, help_text="Fecha en que se cerró el ticket.")

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

    def save(self, *args, **kwargs):
        if self.estado == self.Estado.RESUELTO and not self.fecha_resolucion:
            self.fecha_resolucion = timezone.now()
        if self.estado == self.Estado.CERRADO and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()
        super().save(*args, **kwargs)

    @property
    def tiempo_resolucion(self):
        """Calcula el tiempo que tardó en resolverse el ticket."""
        if self.fecha_resolucion:
            return self.fecha_resolucion - self.fecha_creacion
        return None
        
    @property
    def get_estado_color(self):
        """Devuelve el color correspondiente al estado actual del ticket."""
        colores = {
            self.Estado.ABIERTO: 'primary',
            self.Estado.EN_PROGRESO: 'info',
            self.Estado.PENDIENTE: 'warning',
            self.Estado.RESUELTO: 'success',
            self.Estado.CERRADO: 'secondary'
        }
        return colores.get(self.estado, 'secondary')
        
    @property
    def get_prioridad_color(self):
        """Devuelve el color correspondiente a la prioridad del ticket."""
        colores = {
            self.Prioridad.BAJA: 'success',
            self.Prioridad.MEDIA: 'info',
            self.Prioridad.ALTA: 'warning',
            self.Prioridad.URGENTE: 'danger'
        }
        return colores.get(self.prioridad, 'secondary')
        
    @property
    def get_prioridad_icon(self):
        """Devuelve el icono correspondiente a la prioridad del ticket."""
        iconos = {
            self.Prioridad.BAJA: 'flag text-success',
            self.Prioridad.MEDIA: 'flag text-info',
            self.Prioridad.ALTA: 'flag-checkered text-warning',
            self.Prioridad.URGENTE: 'exclamation-triangle text-danger'
        }
        return iconos.get(self.prioridad, 'flag')

    class Meta:
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"
        ordering = ['-fecha_creacion']


class RespuestaTicket(models.Model):
    """
    Modelo para almacenar las respuestas y seguimientos de un ticket.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta de {self.autor} en ticket #{self.ticket.id}"

    class Meta:
        verbose_name = "Respuesta de Ticket"
        verbose_name_plural = "Respuestas de Tickets"
        ordering = ['fecha_creacion']


def ruta_archivo_adjunto(instance, filename):
    """Genera la ruta de subida para los archivos adjuntos."""
    return f'tickets/{instance.ticket.id}/adjuntos/{filename}'

class ArchivoAdjunto(models.Model):
    """
    Modelo para almacenar archivos adjuntos asociados a un ticket o a una respuesta.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='adjuntos', null=True, blank=True)
    respuesta = models.ForeignKey(RespuestaTicket, on_delete=models.CASCADE, related_name='adjuntos', null=True, blank=True)
    archivo = models.FileField(upload_to=ruta_archivo_adjunto)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def get_filename(self):
        return os.path.basename(self.archivo.name)
        
    @property
    def get_file_icon(self):
        """Devuelve el icono correspondiente al tipo de archivo adjunto."""
        filename = self.get_filename().lower()
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return 'fa-file-image'
        elif filename.endswith('.pdf'):
            return 'fa-file-pdf'
        elif filename.endswith(('.doc', '.docx')):
            return 'fa-file-word'
        elif filename.endswith(('.xls', '.xlsx')):
            return 'fa-file-excel'
        elif filename.endswith(('.ppt', '.pptx')):
            return 'fa-file-powerpoint'
        elif filename.endswith(('.zip', '.rar', '.7z')):
            return 'fa-file-archive'
        elif filename.endswith(('.txt', '.log', '.md')):
            return 'fa-file-alt'
        else:
            return 'fa-file'
    
    @property
    def get_short_name(self):
        """Devuelve un nombre corto para mostrar en la interfaz."""
        filename = self.get_filename()
        if len(filename) > 20:
            name, ext = os.path.splitext(filename)
            return f"{name[:15]}...{ext}"
        return filename

    def __str__(self):
        return self.archivo.name

    class Meta:
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"
