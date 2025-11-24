from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from .models_upgrade import AuditoriaUpgrade, DetalleAuditoriaUpgrade, MatrizCalidadUpgrade, RespuestaAuditoriaUpgrade
from .models import Speech

User = get_user_model()

class AuditoriaUpgradeForm(forms.ModelForm):
    """
    Formulario para crear y editar auditorías de campaña Upgrade
    """
    
    class Meta:
        model = AuditoriaUpgrade
        fields = [
            'agente',
            'numero_telefono', 
            'fecha_llamada',
            'tipo_monitoreo',
            'observaciones'
        ]
        
        widgets = {
            'agente': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Seleccione un agente...'
            }),
            'numero_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el número de teléfono',
                'maxlength': '20'
            }),
            'fecha_llamada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().strftime('%Y-%m-%d')
            }),
            'tipo_monitoreo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones generales de la auditoría upgrade...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo agentes activos para upgrade
        self.fields['agente'].queryset = User.objects.filter(
            is_active=True,
            groups__name__in=['asesor', 'supervisor']
        ).distinct().order_by('first_name', 'last_name')
        
        # Configurar el evaluador automáticamente si está en el contexto
        if hasattr(self, 'request') and self.request.user.is_authenticated:
            self.evaluador = self.request.user
    
    def clean_fecha_llamada(self):
        """
        Validar que la fecha de llamada no sea futura
        """
        fecha_llamada = self.cleaned_data.get('fecha_llamada')
        if fecha_llamada and fecha_llamada > date.today():
            raise forms.ValidationError('La fecha de la llamada no puede ser futura.')
        return fecha_llamada
    
    def clean_numero_telefono(self):
        """
        Validar formato básico del número de teléfono
        """
        numero = self.cleaned_data.get('numero_telefono')
        if numero:
            # Remover espacios y caracteres especiales
            numero_limpio = ''.join(filter(str.isdigit, numero))
            if len(numero_limpio) < 7:
                raise forms.ValidationError('El número de teléfono debe tener al menos 7 dígitos.')
        return numero
    
    def save(self, commit=True):
        """
        Guardar la auditoría upgrade con el evaluador actual
        """
        auditoria = super().save(commit=False)
        
        # Asignar el evaluador si está disponible
        if hasattr(self, 'evaluador'):
            auditoria.evaluador = self.evaluador
        
        if commit:
            auditoria.save()
        
        return auditoria


class DetalleAuditoriaUpgradeForm(forms.ModelForm):
    """
    Formulario para evaluar indicadores específicos de auditorías upgrade
    """
    
    class Meta:
        model = DetalleAuditoriaUpgrade
        fields = ['indicador', 'cumple', 'observaciones']
        
        widgets = {
            'indicador': forms.Select(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'cumple': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones específicas sobre este indicador upgrade...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo indicadores activos de upgrade
        self.fields['indicador'].queryset = MatrizCalidadUpgrade.objects.filter(
            activo=True
        ).order_by('categoria', 'indicador')


class RespuestaAuditoriaUpgradeForm(forms.ModelForm):
    """
    Formulario para que los asesores respondan a indicadores no cumplidos en auditorías upgrade
    """
    
    class Meta:
        model = RespuestaAuditoriaUpgrade
        fields = [
            'tipo_respuesta',
            'respuesta', 
            'compromiso',
            'fecha_compromiso'
        ]
        
        widgets = {
            'tipo_respuesta': forms.Select(attrs={
                'class': 'form-control'
            }),
            'respuesta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escriba su respuesta detallada aquí...',
                'required': True
            }),
            'compromiso': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa su compromiso de mejora (opcional)...'
            }),
            'fecha_compromiso': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            })
        }
    
    def clean_fecha_compromiso(self):
        """
        Validar que la fecha de compromiso no sea pasada
        """
        fecha_compromiso = self.cleaned_data.get('fecha_compromiso')
        if fecha_compromiso and fecha_compromiso < date.today():
            raise forms.ValidationError('La fecha de compromiso no puede ser anterior a hoy.')
        return fecha_compromiso
    
    def clean(self):
        """
        Validaciones cruzadas del formulario
        """
        cleaned_data = super().clean()
        tipo_respuesta = cleaned_data.get('tipo_respuesta')
        compromiso = cleaned_data.get('compromiso')
        fecha_compromiso = cleaned_data.get('fecha_compromiso')
        respuesta = cleaned_data.get('respuesta')
        
        # Validar que la respuesta no esté vacía
        if not respuesta or respuesta.strip() == '':
            raise forms.ValidationError('La respuesta es obligatoria.')
        
        # Si hay compromiso, debe haber fecha de compromiso
        if compromiso and not fecha_compromiso:
            raise forms.ValidationError('Si especifica un compromiso, debe indicar la fecha límite.')
        
        # Si hay fecha de compromiso, debe haber compromiso
        if fecha_compromiso and not compromiso:
            raise forms.ValidationError('Si especifica una fecha de compromiso, debe describir el compromiso.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Guardar la respuesta con el asesor actual
        """
        respuesta = super().save(commit=False)
        
        # El asesor debe ser asignado desde la vista
        if commit:
            respuesta.save()
        
        return respuesta


class MatrizCalidadUpgradeForm(forms.ModelForm):
    """
    Formulario para crear y editar matrices de calidad específicas para upgrade
    """
    
    class Meta:
        model = MatrizCalidadUpgrade
        fields = [
            'tipologia',
            'categoria',
            'indicador',
            'ponderacion',
            'activo'
        ]
        
        widgets = {
            'tipologia': forms.Select(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría para upgrade...'
            }),
            'indicador': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del indicador de calidad para upgrade...'
            }),
            'ponderacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Peso del indicador (0.01 - 100)'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_ponderacion(self):
        """
        Validar que la ponderación esté en el rango correcto
        """
        ponderacion = self.cleaned_data.get('ponderacion')
        if ponderacion is not None:
            if ponderacion < 0.01 or ponderacion > 100:
                raise forms.ValidationError('La ponderación debe estar entre 0.01 y 100.')
        return ponderacion
    
    def save(self, commit=True):
        """
        Guardar la matriz con el usuario de creación
        """
        matriz = super().save(commit=False)
        
        # El usuario de creación debe ser asignado desde la vista
        if commit:
            matriz.save()
        
        return matriz


# FormSet para manejar múltiples detalles de auditoría upgrade
DetalleAuditoriaUpgradeFormSet = forms.modelformset_factory(
    DetalleAuditoriaUpgrade,
    form=DetalleAuditoriaUpgradeForm,
    extra=0,
    can_delete=False
)
