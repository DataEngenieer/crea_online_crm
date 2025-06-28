from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    remitente = models.ForeignKey(User, related_name='mensajes_enviados', on_delete=models.CASCADE)
    destinatario = models.ForeignKey(User, related_name='mensajes_recibidos', on_delete=models.CASCADE, null=True, blank=True)
    mensaje = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    masivo = models.BooleanField(default=False)  # True si es mensaje masivo de supervisor a todos los asesores

    def __str__(self):
        return f"{self.remitente} -> {self.destinatario if self.destinatario else 'Todos los asesores'}: {self.mensaje[:20]}"