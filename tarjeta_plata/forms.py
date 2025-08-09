from django import forms
from django.contrib.auth.models import User
from .models import (
    VentaTarjetaPlata, 
    ClienteTarjetaPlata, 
    AuditoriaBackofficeTarjetaPlata,
    GestionBackofficeTarjetaPlata,
    ESTADO_VENTA_TARJETA_CHOICES
)


class VentaTarjetaPlataForm(forms.ModelForm):
    """Formulario para crear ventas de tarjeta de crédito"""
    
    class Meta:
        model = VentaTarjetaPlata
        fields = [
            'item', 'nombre', 'ine', 'rfc', 'telefono', 'correo', 
            'direccion', 'codigo_postal', 'usuario_c8', 'entrega', 'dn', 
            'estado_republica', 'ingreso_mensual_cliente', 'resultado', 'observaciones'
        ]
        widgets = {
            'item': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese el item del cliente',
                'autocomplete': 'off',
                'required': True
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre completo del cliente',
                'autocomplete': 'off',
                'required': True
            }),
            'ine': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Número de INE',
                'autocomplete': 'off',
                'required': True
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'RFC del cliente',
                'autocomplete': 'off',
                'maxlength': '13',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Teléfono de contacto',
                'autocomplete': 'off',
                'required': True
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'correo@ejemplo.com',
                'autocomplete': 'off',
                'required': True
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Dirección completa del cliente',
                'rows': 3,
                'autocomplete': 'off',
                'required': True
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Código postal',
                'autocomplete': 'off',
                'required': True
            }),
            'usuario_c8': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Usuario C8',
                'autocomplete': 'off'
            }),
            'entrega': forms.Select(attrs={
                'class': 'form-select', 
                'autocomplete': 'off'
            }),
            'dn': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'DN',
                'autocomplete': 'off'
            }),
            'estado_republica': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Estado República',
                'autocomplete': 'off'
            }),
            'ingreso_mensual_cliente': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingreso mensual del cliente',
                'step': '0.01',
                'min': '0',
                'autocomplete': 'off'
            }),
            'resultado': forms.Select(attrs={
                'class': 'form-select', 
                'autocomplete': 'off'
            }),
            'observaciones': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Observaciones adicionales (opcional)',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'item': 'Item',
            'nombre': 'Nombre Completo',
            'ine': 'INE',
            'rfc': 'RFC',
            'telefono': 'Teléfono',
            'correo': 'Correo Electrónico',
            'direccion': 'Dirección',
            'codigo_postal': 'Código Postal',
            'usuario_c8': 'Usuario C8',
            'entrega': 'Tipo de Entrega',
            'dn': 'DN',
            'estado_republica': 'Estado República',
            'ingreso_mensual_cliente': 'Ingreso Mensual Cliente',
            'resultado': 'Resultado',
            'observaciones': 'Observaciones',
        }

    def clean_rfc(self):
        """Validación personalizada para el RFC"""
        rfc = self.cleaned_data.get('rfc')
        if rfc:
            rfc = rfc.upper().strip()
            if len(rfc) < 10 or len(rfc) > 13:
                raise forms.ValidationError('El RFC debe tener entre 10 y 13 caracteres')
        return rfc

    def clean_codigo_postal(self):
        """Validación personalizada para el código postal mexicano"""
        codigo_postal = self.cleaned_data.get('codigo_postal')
        if codigo_postal:
            if not codigo_postal.isdigit() or len(codigo_postal) != 5:
                raise forms.ValidationError('El código postal debe tener exactamente 5 dígitos')
        return codigo_postal


class ClienteTarjetaPlataForm(forms.ModelForm):
    """Formulario para gestión de clientes de tarjeta de crédito"""
    
    class Meta:
        model = ClienteTarjetaPlata
        fields = [
            'item', 'telefono', 'nombre_completo', 'factibilidad', 
            'tipo', 'rfc', 'fecha_nacimiento', 'genero', 'email'
        ]
        widgets = {
            'item': forms.TextInput(attrs={
                'class': 'form-control', 
                'autocomplete': 'off'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control', 
                'autocomplete': 'off'
            }),
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control', 
                'autocomplete': 'off'
            }),
            'factibilidad': forms.Select(attrs={
                'class': 'form-select', 
                'autocomplete': 'off'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select', 
                'autocomplete': 'off'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control', 
                'autocomplete': 'off',
                'maxlength': '13'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'autocomplete': 'off'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-select', 
                'autocomplete': 'off'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'autocomplete': 'off'
            }),
        }


class GestionBackofficeForm(forms.ModelForm):
    """Formulario para gestiones del backoffice"""
    
    # Opciones de estado sin 'nueva' - solo se puede aceptar o rechazar
    ESTADO_GESTION_CHOICES = [
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    
    nuevo_estado = forms.ChoiceField(
        choices=ESTADO_GESTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'autocomplete': 'off'
        }),
        label='Nuevo Estado'
    )
    
    class Meta:
        model = GestionBackofficeTarjetaPlata
        fields = ['comentario', 'archivo_llamada']
        widgets = {
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingrese el comentario de la gestión...',
                'autocomplete': 'off'
            }),
            'archivo_llamada': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*,.mp3,.wav,.m4a,.aac,.ogg',
                'autocomplete': 'off',
                'required': True
            }),
        }
        labels = {
            'comentario': 'Comentario de la Gestión',
            'archivo_llamada': 'Archivo de Llamada (Obligatorio)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer obligatorio el campo archivo_llamada
        self.fields['archivo_llamada'].required = True


class AuditoriaBackofficeForm(forms.ModelForm):
    """Formulario para auditorías del backoffice"""
    
    class Meta:
        model = AuditoriaBackofficeTarjetaPlata
        fields = ['call_review', 'call_upload', 'observaciones_auditoria']
        widgets = {
            'call_review': forms.Select(attrs={
                'class': 'form-select',
                'autocomplete': 'off'
            }),
            'call_upload': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*,.mp3,.wav,.m4a'
            }),
            'observaciones_auditoria': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de la auditoría (opcional)',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'call_review': 'Call Review',
            'call_upload': 'Subir Audio de Llamada',
            'observaciones_auditoria': 'Observaciones de Auditoría',
        }


class CargaMasivaClientesForm(forms.Form):
    """Formulario para carga masiva de clientes desde archivo CSV/Excel"""
    
    archivo = forms.FileField(
        label='Archivo de Clientes',
        help_text='Seleccione un archivo CSV o Excel con los datos de los clientes',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    def clean_archivo(self):
        """Validación del archivo subido"""
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar extensión del archivo
            nombre = archivo.name.lower()
            if not (nombre.endswith('.csv') or nombre.endswith('.xlsx') or nombre.endswith('.xls')):
                raise forms.ValidationError('Solo se permiten archivos CSV o Excel (.csv, .xlsx, .xls)')
            
            # Validar tamaño del archivo (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB')
        
        return archivo


class FiltroVentasForm(forms.Form):
    """Formulario para filtrar ventas en las bandejas"""
    
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Inicio'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Fin'
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + ESTADO_VENTA_TARJETA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    agente = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name__in=['asesor', 'administrador']).distinct(),
        required=False,
        empty_label='Todos los agentes',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Agente'
    )
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, RFC, teléfono...'
        }),
        label='Buscar'
    )