from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Venta, GestionAsesor, GestionBackoffice, TIPO_CLIENTE_CHOICES, SEGMENTO_CHOICES, TIPO_SERVICIO_CHOICES


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['documento', 'nombres', 'apellidos', 'correo', 'departamento', 'ciudad', 
                  'barrio', 'direccion', 'telefono']
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['tipo_cliente', 'plan_adquiere', 'segmento', 'numero_contacto', 'imei', 'fvc', 
                  'fecha_entrega', 'fecha_expedicion', 'origen', 'numero_grabacion', 'selector', 
                  'orden', 'confronta', 'observacion', 'nip']
        widgets = {
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
            'plan_adquiere': forms.TextInput(attrs={'class': 'form-control'}),
            'segmento': forms.Select(attrs={'class': 'form-control'}),
            'numero_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'imei': forms.TextInput(attrs={'class': 'form-control'}),
            'fvc': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'origen': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_grabacion': forms.TextInput(attrs={'class': 'form-control'}),
            'selector': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.TextInput(attrs={'class': 'form-control'}),
            'confronta': forms.FileInput(attrs={'class': 'form-control-file'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nip': forms.TextInput(attrs={'class': 'form-control'}),
        }


class VentaClienteForm(forms.ModelForm):
    # Se usará ModelForm para aprovechar el método save()
    class Meta:
        model = Cliente
        fields = [
            'tipo_documento', 'documento', 'nombres', 'apellidos', 'correo',
            'departamento', 'ciudad', 'barrio', 'direccion', 'telefono'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
        }
    
    # Campos de la venta
    tipo_cliente = forms.ChoiceField(choices=TIPO_CLIENTE_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    plan_adquiere = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    segmento = forms.ChoiceField(choices=SEGMENTO_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    numero_contacto = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    imei = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    fvc = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    fecha_entrega = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}))
    fecha_expedicion = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}))
    origen = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    numero_grabacion = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    selector = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    orden = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    confronta = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    observacion = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'}))
    nip = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))


class GestionAsesorForm(forms.ModelForm):
    class Meta:
        model = GestionAsesor
        fields = ['comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GestionBackofficeForm(forms.ModelForm):
    class Meta:
        model = GestionBackoffice
        fields = ['estado', 'comentario', 'motivo_devolucion', 'campos_corregir']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'motivo_devolucion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'campos_corregir': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar las opciones de estado para backoffice
        self.fields['estado'].choices = [
            ('pendiente_revision', 'Pendiente de Revisión'),
            ('devuelta', 'Devuelta para Corrección'),
            ('aprobada', 'Aprobada'),
            ('digitada', 'Digitada'),
            ('rechazada', 'Rechazada'),
        ]


class CorreccionVentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['tipo_cliente', 'plan_adquiere', 'segmento', 'numero_contacto', 'imei', 'fvc', 
                  'fecha_entrega', 'fecha_expedicion', 'origen', 'numero_grabacion', 'selector', 
                  'orden', 'confronta', 'observacion', 'nip']
        widgets = {
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
            'plan_adquiere': forms.TextInput(attrs={'class': 'form-control'}),
            'segmento': forms.Select(attrs={'class': 'form-control'}),
            'numero_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'imei': forms.TextInput(attrs={'class': 'form-control'}),
            'fvc': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'origen': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_grabacion': forms.TextInput(attrs={'class': 'form-control'}),
            'selector': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.TextInput(attrs={'class': 'form-control'}),
            'confronta': forms.FileInput(attrs={'class': 'form-control-file'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nip': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    comentario = forms.CharField(
        required=True, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Describa las correcciones realizadas"
    )