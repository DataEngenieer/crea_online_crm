from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Cliente, Gestion, GESTION_OPCIONES, ESTADO_CONTACTO_CHOICES, Campana

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
            # Obtener el usuario por email
            user = UserModel.objects.get(email__iexact=email)
            
            # Verificar si el usuario está activo
            if not user.is_active:
                raise forms.ValidationError(
                    "Esta cuenta está inactiva. Por favor contacte al administrador."
                )
                
            # Verificar la contraseña
            if not user.check_password(password):
                raise forms.ValidationError(
                    "Por favor, introduzca un correo y contraseña correctos. "
                    "Observe que ambos campos pueden ser sensibles a mayúsculas."
                )
                
            # Si todo está bien, establecer el nombre de usuario para la autenticación
            self.cleaned_data['username'] = user.username
            
        except UserModel.DoesNotExist:
            # No revelar si el usuario existe o no
            raise forms.ValidationError(
                "Por favor, introduzca un correo y contraseña correctos. "
                "Observe que ambos campos pueden ser sensibles a mayúsculas."
            )
            
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
        required=False,  # Cambiado a no requerido para evitar problemas de validación
        label="Referencia de Producto",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2',
            'data-placeholder': 'Seleccione una referencia',
            'data-allow-clear': 'true'
        }),
        help_text="Seleccione la referencia del producto relacionada con esta gestión"
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
        
        # Inicializar opciones de referencia de producto
        self.fields['referencia_producto'].choices = self.get_referencias_choices(cliente_instance)
        
        # Configurar el resto de los campos
        self.setup_fields()
    
    def get_referencias_choices(self, cliente_instance):
        """Obtiene las opciones de referencia para el cliente"""
        if not cliente_instance:
            return [('', 'No hay referencias disponibles')]
            
        try:
            referencias = Cliente.objects.filter(
                documento=cliente_instance.documento
            ).exclude(referencia__isnull=True).exclude(referencia='').values_list(
                'referencia', flat=True
            ).distinct()
            
            return [('', 'Seleccione una referencia')] + [(ref, ref) for ref in referencias if ref]
            
        except Exception as e:
            print(f"Error al obtener referencias: {str(e)}")
            return [('', 'Error al cargar referencias')]
    
    def setup_fields(self):
        """Configura los campos del formulario"""
        # Configuración común para los campos
        self.fields['estado_contacto'].choices = ESTADO_CONTACTO_CHOICES
        self.fields['estado_contacto'].widget.attrs.update({'class': 'form-select'})
        self.fields['canal_contacto'].widget.attrs.update({'class': 'form-select'})
        
        # Establecer valor predeterminado para canal_contacto si no está definido
        if not self.initial.get('canal_contacto'):
            self.initial['canal_contacto'] = 'telefono'
            
        # Configurar campos condicionales
        self.setup_conditional_fields()
        
    def setup_conditional_fields(self):
        """Configura campos que dependen de otros campos"""
        # Inicializar N1 y N2 vacíos o con opciones si es una instancia existente
        self.fields['tipo_gestion_n1'].choices = [('', 'Seleccione Nivel 1')]
        self.fields['tipo_gestion_n2'].choices = [('', 'Seleccione Nivel 2')]

        if self.instance and self.instance.pk:
            estado_contacto_val = self.instance.estado_contacto
            tipo_gestion_n1_val = self.instance.tipo_gestion_n1

            if estado_contacto_val and estado_contacto_val in GESTION_OPCIONES:
                nivel1_data = GESTION_OPCIONES[estado_contacto_val].get('nivel1', {})
                self.fields['tipo_gestion_n1'].choices = [('', 'Seleccione Nivel 1')] + [(k, v['label']) for k, v in nivel1_data.items()]
                self.fields['tipo_gestion_n1'].initial = tipo_gestion_n1_val

                if tipo_gestion_n1_val and tipo_gestion_n1_val in nivel1_data:
                    nivel2_data = nivel1_data[tipo_gestion_n1_val].get('nivel2', {})
                    self.fields['tipo_gestion_n2'].choices = [('', 'Seleccione Nivel 2')] + [(k, v_label) for k, v_label in nivel2_data.items()]
                    self.fields['tipo_gestion_n2'].initial = self.instance.tipo_gestion_n2
            
            # No deshabilitar si hay instancia, ya que los valores deben estar seleccionados
            self.fields['tipo_gestion_n1'].widget.attrs.pop('disabled', None)
            self.fields['tipo_gestion_n2'].widget.attrs.pop('disabled', None)
        else:  # Formulario nuevo, deshabilitar N1 y N2 inicialmente
            self.fields['tipo_gestion_n1'].widget.attrs['disabled'] = True
            self.fields['tipo_gestion_n2'].widget.attrs['disabled'] = True
        
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
        """Validación personalizada para los campos del formulario."""
        print("\n=== INICIO DE CLEAN DEL FORMULARIO ===")
        print(f"Datos POST recibidos: {self.data}")
        
        cleaned_data = super().clean()
        print(f"Datos limpios: {cleaned_data}")
        
        estado_contacto = cleaned_data.get('estado_contacto')
        tipo_gestion_n1 = cleaned_data.get('tipo_gestion_n1')
        referencia_producto = cleaned_data.get('referencia_producto')
        
        print(f"Estado contacto: {estado_contacto}")
        print(f"Tipo gestión N1: {tipo_gestion_n1}")
        print(f"Referencia producto: {referencia_producto}")
        print(f"Choices de referencia: {dict(self.fields['referencia_producto'].choices).keys() if 'referencia_producto' in self.fields else 'No hay campo referencia_producto'}")

        # Validar que si se seleccionó un estado de contacto, también se seleccione tipo_gestion_n1
        if estado_contacto and not tipo_gestion_n1:
            self.add_error('tipo_gestion_n1', 'Debe seleccionar un tipo de gestión')
            
        # Validar referencia de producto solo para acuerdos de pago (AP o PP)
        if estado_contacto == 'contacto_efectivo':
            # Solo requerir referencia para acuerdos de pago
            if tipo_gestion_n1 in ['AP', 'PP']:
                if not referencia_producto:
                    self.add_error('referencia_producto', 'Debe seleccionar una referencia de producto para acuerdos de pago')
                else:
                    # Asegurarse de que la referencia sea válida
                    choices = dict(self.fields['referencia_producto'].choices).keys() if 'referencia_producto' in self.fields else []
                    if referencia_producto not in choices:
                        self.add_error('referencia_producto', 'La referencia seleccionada no es válida')
                    else:
                        # Forzar el guardado de la referencia en los datos limpios
                        cleaned_data['referencia_producto'] = referencia_producto
                
                # Marcar automáticamente acuerdo_pago_realizado para AP o PP
                cleaned_data['acuerdo_pago_realizado'] = True

        # Validación para contactos efectivos
        if estado_contacto == 'contacto_efectivo':
            # Hacer que la fecha de pago efectivo sea opcional temporalmente
            # if not cleaned_data.get('fecha_pago_efectivo'):
            #     self.add_error('fecha_pago_efectivo', 'Debe ingresar la fecha de pago efectivo')
            
            # Validar campos de acuerdo solo si se están enviando
            if tipo_gestion_n1 in ['PP', 'AP']:  # Pago Parcial o Acuerdo de Pago
                fecha_acuerdo = cleaned_data.get('fecha_acuerdo')
                monto_acuerdo = cleaned_data.get('monto_acuerdo')
                
                # Solo validar si se envió algún dato de acuerdo
                if fecha_acuerdo or monto_acuerdo:
                    if not fecha_acuerdo:
                        self.add_error('fecha_acuerdo', 'Si ingresa un monto, debe especificar la fecha del acuerdo')
                    if not monto_acuerdo or float(monto_acuerdo) <= 0:
                        self.add_error('monto_acuerdo', 'Debe especificar un monto válido para el acuerdo')
                
                # Las observaciones son opcionales
                # if not cleaned_data.get('observaciones_acuerdo'):
                #     self.add_error('observaciones_acuerdo', 'Recomendamos ingresar observaciones sobre el acuerdo')
        
        return cleaned_data
