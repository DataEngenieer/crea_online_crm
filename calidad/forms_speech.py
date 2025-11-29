# calidad/forms_speech.py
from django import forms
from .models import MatrizCalidad, Speech

class SpeechForm(forms.ModelForm):
    class Meta:
        model = Speech
        fields = ['audio']

class MatrizCalidadForm(forms.ModelForm):
    ponderacion = forms.DecimalField(max_digits=5, decimal_places=2, min_value=-100, max_value=100)
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
                'min': '-100',
                'max': '100',
                'step': '0.01',
                'placeholder': '-100 a 100'
            }),
        }

    def clean_ponderacion(self):
        ponderacion = self.cleaned_data.get('ponderacion')
        if ponderacion is None:
            raise forms.ValidationError('La ponderación es requerida')
        if ponderacion < -100 or ponderacion > 100:
            raise forms.ValidationError('La ponderación debe estar entre -100 y 100')
        return ponderacion
