from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Cliente

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-MAIL",
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'usuario@ejemplo.com'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email__iexact=email)
            self.cleaned_data['username'] = user.username
        except UserModel.DoesNotExist:
            pass  # El AuthenticationForm se encargará del error
        return super().clean()


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'documento', 'tipo_documento', 'nombre_completo', 
            'ciudad', 'celular_1', 'email', 'direccion_1', 
            'referencia', 'principal', 'deuda_total', 'fecha_cesion',
            'observaciones_adicionales'
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'principal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Deuda Principal'}),
            'deuda_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Deuda Total'}),
            'fecha_cesion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Widget para fecha
            'celular_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Celular'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'direccion_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección Principal'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}), 
            'observaciones_adicionales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campo referencia es obligatorio y con placeholder específico
        self.fields['referencia'].required = True
        self.fields['referencia'].widget.attrs.update({'placeholder': 'Referencia del producto'}) 

        # Lista de campos que serán opcionales en el formulario, aunque sean obligatorios en el modelo por defecto
        # Los campos que SÍ son opcionales en el modelo (ej. ciudad, email) no necesitan estar aquí para ser opcionales en el form.
        optional_in_form = ['ciudad', 'email', 'direccion_1', 'observaciones_adicionales', 'fecha_cesion'] 

        for field_name, field in self.fields.items():
            # Aplicar la clase form-control a todos los campos
            if not field.widget.attrs.get('class'):
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['class'] = 'form-control'
                    if not field.widget.attrs.get('rows'):
                        field.widget.attrs['rows'] = 3 
                else:
                    field.widget.attrs['class'] = 'form-control'
            
            # Marcar campos como no requeridos en el HTML si están en nuestra lista de opcionales
            # o si el campo del modelo subyacente permite blank=True
            if field_name in optional_in_form or (hasattr(field.widget, 'input_type') and field.widget.input_type != 'file' and getattr(self.Meta.model._meta.get_field(field_name), 'blank', False)):
                field.required = False
            elif not getattr(self.Meta.model._meta.get_field(field_name), 'blank', False) and not getattr(self.Meta.model._meta.get_field(field_name), 'null', False):
                # Si el modelo lo tiene como no blank y no null, es requerido
                field.required = True

        # Asegurarse de que 'referencia' sea siempre requerido en el formulario
        self.fields['referencia'].required = True
        # Asegurarse de que 'principal' y 'deuda_total' sean requeridos (ya no son opcionales)
        self.fields['principal'].required = True
        self.fields['deuda_total'].required = True
        # Asegurarse de que 'celular_1' sea requerido
        self.fields['celular_1'].required = True
        # fecha_cesion es opcional por defecto por el modelo (blank=True, null=True) y está en optional_in_form

        # Configuración específica para el campo tipo_documento
        self.fields['tipo_documento'].choices = [
            ('CC', 'Cédula de Ciudadanía'),
            ('CE', 'Cédula de Extranjería'),
            ('NIT', 'Número de Identificación Tributaria'),
            ('PAS', 'Pasaporte'),
            ('RC', 'Registro Civil'),
            ('TI', 'Tarjeta de Identidad'),
        ]
