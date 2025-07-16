from django import forms
from django.contrib.auth.models import User
from .models import VentaPortabilidad, VentaPrePos, VentaUpgrade, GestionAsesor, GestionBackoffice, Planes_portabilidad


class VentaPortabilidadForm(forms.ModelForm):
    class Meta:
        model = VentaPortabilidad
        fields = [
            'tipo_documento', 'documento', 'fecha_expedicion', 'nombres', 'apellidos',
            'telefono_legalizacion', 'plan_adquiere', 'numero_a_portar', 'nip', 'fecha_entrega',
            'fecha_ventana_cambio', 'numero_orden', 'base_origen', 'usuario_greta', 'confronta', 'observacion'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_a_portar': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nip': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'fecha_ventana_cambio': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'base_origen': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'usuario_greta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'confronta': forms.FileInput(attrs={'class': 'form-control-file'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    # Método para inicializar el formulario con valores por defecto o personalizados
    def __init__(self, *args, **kwargs):
        # Extraer el parámetro user si existe
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Obtener solo los planes activos de tipo portabilidad para el selector
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo', tipo_plan='portabilidad')


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
        fields = ['comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar las opciones de estado para backoffice


class VentaPrePosForm(forms.ModelForm):
    class Meta:
        model = VentaPrePos
        fields = [
            'tipo_cliente', 'tipo_documento', 'documento', 'fecha_expedicion', 'nombres', 'apellidos',
            'telefono_legalizacion', 'plan_adquiere', 'numero_orden', 'base_origen', 'usuario_greta', 'observacion'
        ]
        widgets = {
            'tipo_cliente': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'base_origen': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'usuario_greta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filtrar solo planes activos de tipo prepos
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo', tipo_plan='prepos')


class VentaUpgradeForm(forms.ModelForm):
    class Meta:
        model = VentaUpgrade
        fields = [
            'tipo_cliente', 'tipo_documento', 'documento', 'fecha_expedicion', 'nombres', 'apellidos',
            'telefono_legalizacion', 'codigo_verificacion', 'plan_adquiere', 'numero_orden', 
            'base_origen', 'usuario_greta', 'observacion'
        ]
        widgets = {
            'tipo_cliente': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'codigo_verificacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'base_origen': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'usuario_greta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filtrar solo planes activos de tipo upgrade
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo', tipo_plan='upgrade')


class PlanesPortabilidadForm(forms.ModelForm):
    """Formulario para la gestión de planes de portabilidad"""
    class Meta:
        model = Planes_portabilidad
        fields = ['codigo','nombre_plan', 'caracteristicas', 'CFM', 'CFM_sin_iva', 'tipo_plan', 'estado']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_plan': forms.TextInput(attrs={'class': 'form-control'}),
            'caracteristicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'CFM': forms.NumberInput(attrs={'class': 'form-control'}),
            'CFM_sin_iva': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_plan': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class CorreccionVentaForm(forms.ModelForm):
    """Formulario para corregir ventas devueltas por backoffice"""
    class Meta:
        model = VentaPortabilidad
        fields = [
            'tipo_cliente', 'tipo_documento', 'documento', 'fecha_expedicion', 'nombres', 'apellidos',
            'telefono_legalizacion', 'plan_adquiere', 'numero_a_portar', 'nip', 'fecha_entrega',
            'fecha_ventana_cambio', 'numero_orden', 'base_origen', 'usuario_greta', 'confronta', 'observacion'
        ]
        widgets = {
            'tipo_cliente': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_a_portar': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nip': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'fecha_ventana_cambio': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'base_origen': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'usuario_greta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'confronta': forms.FileInput(attrs={'class': 'form-control-file'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener solo los planes activos para el selector
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo')