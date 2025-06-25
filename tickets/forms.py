from django import forms
from .models import Ticket, RespuestaTicket, ArchivoAdjunto

class TicketForm(forms.ModelForm):
    """
    Formulario para la creación y edición de tickets de soporte.
    """
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'tipo', 'prioridad', 'asignado_a']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Problema al generar reporte de ventas'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe el problema o requerimiento con el mayor detalle posible...'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'asignado_a': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'titulo': 'Asunto',
            'descripcion': 'Descripción detallada',
            'tipo': 'Tipo de solicitud',
            'prioridad': 'Prioridad',
            'asignado_a': 'Asignar a',
        }

class RespuestaTicketForm(forms.ModelForm):
    """
    Formulario para añadir una respuesta a un ticket existente.
    """
    class Meta:
        model = RespuestaTicket
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe tu respuesta o comentario aquí...'}),
        }
        labels = {
            'mensaje': 'Respuesta'
        }

