from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Auditoria, MatrizCalidad, RespuestaAuditoria

User = get_user_model()

class AuditoriaForm(forms.ModelForm):
    """
    Formulario para crear y editar auditorías de calidad
    """
    class Meta:
        model = Auditoria
        fields = [
            'agente', 'numero_telefono', 'fecha_llamada',
            'tipo_monitoreo', 'observaciones'
        ]
        widgets = {
            'fecha_llamada': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                },
                format='%Y-%m-%d'
            ),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese observaciones generales de la auditoría'
            }),

            'agente': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Buscar agente...',
            }),
            'tipo_monitoreo': forms.Select(attrs={'class': 'form-select'}),
            'numero_telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
        


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios activos para el campo agente
        self.fields['agente'].queryset = User.objects.filter(
            is_active=True
        ).exclude(id=user.id if user else None)
        # Mostrar nombre y apellido en el <option> del select
        self.fields['agente'].label_from_instance = lambda obj: (f"{obj.first_name} {obj.last_name}".strip() or obj.username)
        

        
        # Establecer valores por defecto
        if not self.instance.pk:
            self.initial['fecha_llamada'] = timezone.now().strftime('%Y-%m-%d')
            
        # Configurar el widget Select2 para el campo agente
        self.fields['agente'].widget.attrs.update({
            'class': 'form-select select2',
            'data-allow-clear': 'true',
            'data-minimum-input-length': 2,
            'data-ajax--cache': 'true',
        })


class RespuestaAuditoriaForm(forms.ModelForm):
    """
    Formulario para que los asesores respondan a indicadores no cumplidos
    """
    class Meta:
        model = RespuestaAuditoria
        fields = [
            'tipo_respuesta', 'respuesta', 'compromiso', 'fecha_compromiso'
        ]
        widgets = {
            'tipo_respuesta': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'respuesta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe tu respuesta, explicación o plan de acción para este indicador...',
                'required': True
            }),
            'compromiso': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe tu compromiso específico de mejora (opcional)...'
            }),
            'fecha_compromiso': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%d')
            })
        }
        labels = {
            'tipo_respuesta': 'Tipo de respuesta',
            'respuesta': 'Tu respuesta',
            'compromiso': 'Compromiso de mejora',
            'fecha_compromiso': 'Fecha límite del compromiso'
        }
        help_texts = {
            'tipo_respuesta': 'Selecciona el tipo de respuesta que mejor describa tu situación',
            'respuesta': 'Explica tu punto de vista, las acciones que tomarás o las aclaraciones necesarias',
            'compromiso': 'Si aplica, describe un compromiso específico de mejora',
            'fecha_compromiso': 'Fecha en la que te comprometes a implementar la mejora'
        }
    
    def __init__(self, *args, **kwargs):
        self.auditoria = kwargs.pop('auditoria', None)
        self.detalle_auditoria = kwargs.pop('detalle_auditoria', None)
        self.asesor = kwargs.pop('asesor', None)
        super().__init__(*args, **kwargs)
        
        # Configurar fecha mínima para el compromiso
        self.fields['fecha_compromiso'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%d')
        
        # Hacer campos requeridos condicionalmente
        if self.instance.pk:
            # Si es una edición, mantener los valores actuales
            pass
        else:
            # Para nuevas respuestas, hacer respuesta obligatoria
            self.fields['respuesta'].required = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asignar relaciones si están disponibles
        if self.auditoria:
            instance.auditoria = self.auditoria
        if self.detalle_auditoria:
            instance.detalle_auditoria = self.detalle_auditoria
        if self.asesor:
            instance.asesor = self.asesor
        
        if commit:
            instance.save()
        return instance
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_respuesta = cleaned_data.get('tipo_respuesta')
        compromiso = cleaned_data.get('compromiso')
        fecha_compromiso = cleaned_data.get('fecha_compromiso')
        
        # Validar que si hay compromiso, debe haber fecha
        if compromiso and not fecha_compromiso:
            raise forms.ValidationError(
                'Si especificas un compromiso, debes indicar una fecha límite.'
            )
        
        # Validar que la fecha de compromiso sea futura
        if fecha_compromiso and fecha_compromiso <= timezone.now().date():
            raise forms.ValidationError(
                'La fecha de compromiso debe ser posterior a hoy.'
            )
        
        return cleaned_data