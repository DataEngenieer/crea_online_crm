# calidad/forms_speech.py
from django import forms
from .models import MatrizCalidad, Speech

class SpeechForm(forms.ModelForm):
    class Meta:
        model = Speech
        fields = ['audio']

class MatrizCalidadForm(forms.ModelForm):
    class Meta:
        model = MatrizCalidad
        fields = [
            'tipologia', 'categoria', 'indicador', 'ponderacion', 'activo'
        ]
        widgets = {
            'tipologia': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la categoría'
            }),
            'indicador': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Ingrese la descripción del indicador'
            }),
            'ponderacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.01 - 100'
            }),
        }

    def clean_ponderacion(self):
        ponderacion = self.cleaned_data.get('ponderacion')
        if ponderacion is not None and (ponderacion <= 0 or ponderacion > 100):
            raise forms.ValidationError('La ponderación debe estar entre 0.01 y 100')
        return ponderacion