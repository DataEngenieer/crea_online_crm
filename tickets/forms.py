from django import forms
from django.core.validators import FileExtensionValidator
from .models import Ticket, RespuestaTicket, ArchivoAdjunto

class TicketForm(forms.ModelForm):
    """
    Formulario para la creación y edición de tickets de soporte.
    """
    # Campo para archivos adjuntos (no está en el modelo, se maneja en la vista)
    # Usamos un campo simple sin widget personalizado
    archivos = forms.FileField(
        required=False,
        label='Archivos adjuntos',
        # No especificamos widget con atributo multiple aquí
        # Lo haremos manualmente en la plantilla HTML
    )
    
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'tipo', 'prioridad', 'asignado_a']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Problema al generar reporte de ventas',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Describe el problema o requerimiento con el mayor detalle posible...',
                'required': True
            }),
            'tipo': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'prioridad': forms.Select(attrs={'class': 'form-select', 'required': True}),
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

