from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Cliente, Gestion, GESTION_OPCIONES, ESTADO_CONTACTO_CHOICES

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
        cliente_instance = kwargs.pop('cliente_instance', None) # Obtener la instancia del cliente
        super().__init__(*args, **kwargs)

        if cliente_instance:
            # Filtrar las referencias de producto por cliente
            self.fields['referencia_producto'].queryset = Cliente.objects.filter(pk=cliente_instance.pk)
        
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


class GestionForm(forms.ModelForm):
    # Usamos CharField para evitar la validación estricta de opciones pero mantenemos el widget Select
    tipo_gestion_n1 = forms.CharField(
        required=True,  # Ahora es obligatorio
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo_gestion_n2 = forms.CharField(
        required=False,  # Ya no es obligatorio
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Campos para acuerdo de pago
    fecha_acuerdo = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    monto_acuerdo = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    observaciones_acuerdo = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))
    referencia_producto = forms.ChoiceField(
        choices=[],
        required=True,
        label="Referencia de Producto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Campos para pago efectivo
    comprobante_pago = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    fecha_pago_efectivo = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    
    fecha_proximo_seguimiento = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    hora_proximo_seguimiento = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    observaciones_generales = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))

    class Meta:
        model = Gestion
        fields = [
            'cliente', 'canal_contacto', 'estado_contacto',
            'tipo_gestion_n1', 'tipo_gestion_n2',
            'acuerdo_pago_realizado', 'fecha_acuerdo', 'monto_acuerdo', 'observaciones_acuerdo', 'referencia_producto',
            'seguimiento_requerido', 'fecha_proximo_seguimiento', 'hora_proximo_seguimiento',
            'observaciones_generales', 'observaciones', 'comprobante_pago', 'fecha_pago_efectivo',
        ]
        widgets = {
            'cliente': forms.HiddenInput(),
            'canal_contacto': forms.Select(attrs={'class': 'form-select'}),
            'estado_contacto': forms.Select(attrs={'class': 'form-select', 'id': 'id_estado_contacto'}), # Usar ESTADO_CONTACTO_CHOICES
            'acuerdo_pago_realizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'seguimiento_requerido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        cliente_instance = kwargs.pop('cliente_instance', None) # Obtener la instancia del cliente
        super().__init__(*args, **kwargs)
        
        if cliente_instance:
            print("DOCUMENTO DEL CLIENTE EN FORM:", cliente_instance.documento)
            doc = cliente_instance.documento
            referencias = (
                Cliente.objects
                .filter(documento=doc)
                .values_list('referencia', flat=True)
                .distinct()
            )
            print("REFERENCIAS ENCONTRADAS EN BD:", list(referencias))
            self.fields['referencia_producto'].choices = [(ref, ref) for ref in referencias if ref]
        else:
            print("NO HAY cliente_instance PASADO AL FORMULARIO")
            self.fields['referencia_producto'].choices = []
        
        self.fields['estado_contacto'].choices = ESTADO_CONTACTO_CHOICES
        self.fields['estado_contacto'].widget.attrs.update({'class': 'form-select'})
        self.fields['canal_contacto'].widget.attrs.update({'class': 'form-select'})
        
        # Establecer "telefono" como valor predeterminado para canal_contacto
        if not self.initial.get('canal_contacto'):
            self.initial['canal_contacto'] = 'telefono'

        # Inicializar N1 y N2 vacíos o con opciones si es una instancia existente
        self.fields['tipo_gestion_n1'].choices = [('', 'Seleccione Nivel 1')]
        self.fields['tipo_gestion_n2'].choices = [('', 'Seleccione Nivel 2')]

        if self.instance and self.instance.pk:
            estado_contacto_val = self.instance.estado_contacto
            tipo_gestion_n1_val = self.instance.tipo_gestion_n1
            # tipo_gestion_n2_val = self.instance.tipo_gestion_n2 # No es necesario para cargar N2, se usa n1_val

            if estado_contacto_val and estado_contacto_val in GESTION_OPCIONES:
                nivel1_data = GESTION_OPCIONES[estado_contacto_val].get('nivel1', {})
                self.fields['tipo_gestion_n1'].choices = [('', 'Seleccione Nivel 1')] + [(k, v['label']) for k, v in nivel1_data.items()]
                self.fields['tipo_gestion_n1'].initial = tipo_gestion_n1_val # Establecer valor inicial

                if tipo_gestion_n1_val and tipo_gestion_n1_val in nivel1_data:
                    nivel2_data = nivel1_data[tipo_gestion_n1_val].get('nivel2', {})
                    self.fields['tipo_gestion_n2'].choices = [('', 'Seleccione Nivel 2')] + [(k, v_label) for k, v_label in nivel2_data.items()]
                    self.fields['tipo_gestion_n2'].initial = self.instance.tipo_gestion_n2 # Establecer valor inicial
            
            # No deshabilitar si hay instancia, ya que los valores deben estar seleccionados
            self.fields['tipo_gestion_n1'].widget.attrs.pop('disabled', None)
            self.fields['tipo_gestion_n2'].widget.attrs.pop('disabled', None)

        else: # Formulario nuevo, deshabilitar N1 y N2 inicialmente
            self.fields['tipo_gestion_n1'].widget.attrs['disabled'] = True
            self.fields['tipo_gestion_n2'].widget.attrs['disabled'] = True
        
        no_requeridos = [
            'fecha_acuerdo', 'monto_acuerdo', 'observaciones_acuerdo',
            'fecha_proximo_seguimiento', 'hora_proximo_seguimiento',
            'observaciones_generales'
        ]
        
        for campo in no_requeridos:
            if campo in self.fields:
                 self.fields[campo].required = False
    
    def clean(self):
        """Validación personalizada para campos condicionales según el tipo_gestion_n2 seleccionado."""
        cleaned_data = super().clean()
        tipo_gestion_n1 = cleaned_data.get('tipo_gestion_n1')
        tipo_gestion_n2 = cleaned_data.get('tipo_gestion_n2')
        
        # Validación básica: comprobar que no sean valores vacíos
        if not tipo_gestion_n1 or tipo_gestion_n1 == '':
            self.add_error('tipo_gestion_n1', 'Debe seleccionar una opción válida de Nivel 1.')
            
        # Ya no validamos tipo_gestion_n2 como obligatorio
        # if not tipo_gestion_n2 or tipo_gestion_n2 == '':
        #    self.add_error('tipo_gestion_n2', 'Debe seleccionar una opción válida de Nivel 2.')
        
        # Validaciones condicionales según tipo_gestion_n2
        if tipo_gestion_n2 == 'PAGADO':
            # Si es PAGADO, debe incluir comprobante y fecha de pago
            comprobante_pago = cleaned_data.get('comprobante_pago')
            fecha_pago_efectivo = cleaned_data.get('fecha_pago_efectivo')
            
            if not comprobante_pago:
                self.add_error('comprobante_pago', 'Debe adjuntar un comprobante de pago cuando selecciona PAGADO.')
                
            if not fecha_pago_efectivo:
                self.add_error('fecha_pago_efectivo', 'Debe ingresar la fecha de pago efectivo cuando selecciona PAGADO.')
        
        elif tipo_gestion_n2 in ['AP', 'PP']:
            # Si es AP o PP, debe marcar acuerdo de pago y completar sus campos
            acuerdo_pago_realizado = cleaned_data.get('acuerdo_pago_realizado')
            fecha_acuerdo = cleaned_data.get('fecha_acuerdo')
            monto_acuerdo = cleaned_data.get('monto_acuerdo')
            
            # Forzar que se active el checkbox de acuerdo de pago
            if not acuerdo_pago_realizado:
                cleaned_data['acuerdo_pago_realizado'] = True
                
            # Validar que se completen los campos del acuerdo
            if not fecha_acuerdo:
                self.add_error('fecha_acuerdo', 'Debe ingresar la fecha del acuerdo para AP o PP.')
                
            if not monto_acuerdo:
                self.add_error('monto_acuerdo', 'Debe ingresar el monto del acuerdo para AP o PP.')
        
        elif tipo_gestion_n2 == 'SOLICITA_LLAMADA':
            # Si solicita llamada posterior, debe activar seguimiento
            seguimiento_requerido = cleaned_data.get('seguimiento_requerido')
            fecha_proximo_seguimiento = cleaned_data.get('fecha_proximo_seguimiento')
            hora_proximo_seguimiento = cleaned_data.get('hora_proximo_seguimiento')
            
            # Forzar que se active el checkbox de seguimiento
            if not seguimiento_requerido:
                cleaned_data['seguimiento_requerido'] = True
                
            # Validar que se completen los campos de seguimiento
            if not fecha_proximo_seguimiento:
                self.add_error('fecha_proximo_seguimiento', 'Debe ingresar la fecha del próximo seguimiento.')
                
            if not hora_proximo_seguimiento:
                self.add_error('hora_proximo_seguimiento', 'Debe ingresar la hora del próximo seguimiento.')
            
        return cleaned_data
