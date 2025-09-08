from django import forms
from django.contrib.auth.models import User
from .models import VentaPortabilidad, VentaPrePos, VentaUpgrade, ClientesUpgrade, ClientesPrePos, GestionAsesor, GestionBackoffice, Planes_portabilidad, Agendamiento, GestionAgendamiento


class VentaPortabilidadForm(forms.ModelForm):
    # Campo personalizado para subida directa a MinIO
    confronta = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'}),
        help_text='Archivo que se subirá directamente a MinIO'
    )
    
    class Meta:
        model = VentaPortabilidad
        fields = [
            'tipo_documento', 'documento', 'fecha_expedicion', 'nombre_completo',
            'telefono_legalizacion', 'plan_adquiere', 'numero_a_portar', 'nip', 'fecha_entrega',
            'fecha_ventana_cambio', 'numero_orden', 'observacion'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_a_portar': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nip': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'fecha_ventana_cambio': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
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


class AgendamientoForm(forms.ModelForm):
    class Meta:
        model = Agendamiento
        fields = [
            'tipo_venta', 'nombre_cliente', 'telefono_contacto', 'fecha_volver_a_llamar',
            'hora_volver_a_llamar', 'observaciones', 'Estado_agendamiento'
        ]
        widgets = {
            'tipo_venta': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_volver_a_llamar': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'hora_volver_a_llamar': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'autocomplete': 'off'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'}),
            'Estado_agendamiento': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Establecer valor por defecto para el estado del agendamiento
        self.fields['Estado_agendamiento'].initial = 'agendado'


class GestionAgendamientoForm(forms.ModelForm):
    class Meta:
        model = GestionAgendamiento
        fields = ['comentario', 'estado_nuevo']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado_nuevo': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.agendamiento = kwargs.pop('agendamiento', None)
        super().__init__(*args, **kwargs)
        
        # Si el agendamiento existe, guardamos su estado actual para usarlo como estado_anterior
        if self.agendamiento:
            self.instance.estado_anterior = self.agendamiento.Estado_agendamiento


class ClientesPrePosForm(forms.ModelForm):
    class Meta:
        model = ClientesPrePos
        fields = ['telefono']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
        }

class VentaPrePosForm(forms.ModelForm):
    class Meta:
        model = VentaPrePos
        fields = [
            'tipo_documento', 'documento', 'fecha_expedicion', 'nombre_completo',
            'telefono_legalizacion', 'plan_adquiere', 'numero_orden', 'observacion'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filtrar solo planes activos de tipo prepos
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo', tipo_plan='prepos')
        # Excluir explícitamente el campo tipo_cliente del formulario
        if 'tipo_cliente' in self.fields:
            del self.fields['tipo_cliente']


class ClientesUpgradeForm(forms.ModelForm):
    class Meta:
        model = ClientesUpgrade
        fields = [
            'id_base', 'nro_registro', 'campana', 'grupo_campana', 'estrategia', 'nombre_cliente',
            'tipo_documento', 'documento', 'direccion', 'estrato', 'barrio', 'departamento',
            'ciudad', 'producto', 'puertos_disponibles', 'promedio_fact', 'mx_tenencia_cuenta',
            'tel_contacto_1', 'tel_contacto_2', 'tel_contacto_3', 'celular_contacto'
        ]
        widgets = {
            'id_base': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nro_registro': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'campana': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'grupo_campana': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'estrategia': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'estrato': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'autocomplete': 'off'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'producto': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'puertos_disponibles': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'promedio_fact': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'mx_tenencia_cuenta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'tel_contacto_1': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'tel_contacto_2': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'tel_contacto_3': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'celular_contacto': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
        }

class VentaUpgradeForm(forms.ModelForm):
    class Meta:
        model = VentaUpgrade
        fields = [
            'cliente_base', 'tipo_documento', 'documento', 'fecha_expedicion', 'nombre_completo',
            'telefono_legalizacion', 'valor_plan_anterior', 'plan_adquiere', 'numero_orden', 'observacion'
        ]
        widgets = {
            'cliente_base': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'valor_plan_anterior': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
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
    # Campo personalizado para subida directa a MinIO
    confronta = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'}),
        help_text='Archivo que se subirá directamente a MinIO (opcional - solo si desea reemplazar el actual)'
    )
    
    class Meta:
        model = VentaPortabilidad
        fields = [
            'tipo_documento', 'documento', 'fecha_expedicion', 'nombre_completo',
            'telefono_legalizacion', 'plan_adquiere', 'numero_a_portar', 'nip', 'fecha_entrega',
            'fecha_ventana_cambio', 'numero_orden', 'base_origen', 'usuario_greta', 'observacion'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_expedicion': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'telefono_legalizacion': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'plan_adquiere': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'}),
            'numero_a_portar': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'nip': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'fecha_ventana_cambio': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date', 'autocomplete': 'off'}),
            'numero_orden': forms.NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'base_origen': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'usuario_greta': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'autocomplete': 'off'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener solo los planes activos para el selector
        self.fields['plan_adquiere'].queryset = Planes_portabilidad.objects.filter(estado='activo')