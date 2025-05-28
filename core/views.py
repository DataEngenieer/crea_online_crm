from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponseForbidden, FileResponse, Http404
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from functools import wraps
from datetime import datetime, timedelta
import os
import re
import pandas as pd
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db import IntegrityError

from .models import *
from .forms import EmailAuthenticationForm, ClienteForm

from django.contrib.auth.views import LoginView, LogoutView

class LoginAuditoriaView(LoginView):
    template_name = 'core/login.html'
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        ip = self.request.META.get('REMOTE_ADDR')
        LoginUser.registrar(user, tipo='login', ip=ip)
        return response

class LogoutAuditoriaView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            ip = self.request.META.get('REMOTE_ADDR')
            LoginUser.registrar(user, tipo='logout', ip=ip)
        return super().dispatch(request, *args, **kwargs)

class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        label="Nombres",
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese sus nombres',
            'autocomplete': 'given-name',
        })
    )
    last_name = forms.CharField(
        required=True,
        label="Apellidos",
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese sus apellidos',
            'autocomplete': 'family-name',
        })
    )
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'usuario@ejemplo.com',
            'autocomplete': 'email',
        })
    )
    username = forms.CharField(
        label="Usuario (documento)",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Número de documento',
            'autocomplete': 'username',
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2')
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg rounded-start-0',
            'placeholder': 'Contraseña',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg rounded-start-0',
            'placeholder': 'Confirmar contraseña',
            'autocomplete': 'new-password',
        })
    )
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        return email

def registro_usuario(request):
    # Permitir acceso incluso si está autenticado
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Asignar al grupo 'empleado' automáticamente
            from django.contrib.auth.models import Group
            grupo, creado = Group.objects.get_or_create(name='colaborador')
            user.groups.add(grupo)
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'core/registro.html', {'form': form})
def inicio(request):
    return render(request, 'core/inicio.html')

def es_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact='Administrador').exists()

@login_required
def clientes(request):
    q = request.GET.get('q', '').strip()

    # Obtener todos los clientes, ordenados para que el 'representante' del grupo sea el más reciente
    clientes_lista_completa = Cliente.objects.all().order_by('documento', '-fecha_registro')

    if q:
        # Filtrar basado en el término de búsqueda q sobre campos individuales de las referencias
        clientes_lista_completa = clientes_lista_completa.filter(
            Q(nombre_completo__icontains=q) |
            Q(documento__icontains=q) |
            Q(referencia__icontains=q) | # Permite buscar una referencia específica y encontrar el grupo
            Q(email__icontains=q) |
            Q(telefono_celular__icontains=q)
        )

    clientes_info_agrupada = {}
    documentos_ya_procesados_por_q = set() # Para asegurar que un documento aparezca solo una vez si q coincide con múltiples referencias

    for cliente_ref in clientes_lista_completa:
        doc = cliente_ref.documento
        if q and doc in documentos_ya_procesados_por_q and doc in clientes_info_agrupada:
            # Si estamos filtrando y ya hemos añadido este documento (a través de otra referencia que coincidió con q)
            # solo incrementamos el contador de referencias del grupo existente.
            clientes_info_agrupada[doc]['num_referencias_coincidentes_q'] = clientes_info_agrupada[doc].get('num_referencias_coincidentes_q', 0) +1
            continue # Ya hemos tomado los datos del representante de este documento.
        
        if doc not in clientes_info_agrupada:
            clientes_info_agrupada[doc] = {
                'documento': doc,
                'nombre_completo': cliente_ref.nombre_completo, # Nombre de la referencia más reciente del grupo
                'email': cliente_ref.email, # Email de la referencia más reciente del grupo
                'num_referencias': 0, # Este será el conteo total de referencias para este documento
                'fecha_registro_grupo': cliente_ref.fecha_registro, # Fecha de la ref más reciente del grupo
                # 'id_representativo': cliente_ref.id # Podríamos usar el documento para el enlace a detalle
            }
            if q:
                documentos_ya_procesados_por_q.add(doc)
        
        # El conteo de num_referencias se hará después, sobre el queryset sin filtro q, para obtener el total real.

    # Obtener el conteo total de referencias para cada documento que está en nuestra lista filtrada (si q existe)
    documentos_en_vista = list(clientes_info_agrupada.keys())
    
    if documentos_en_vista:
        conteos_referencias = Cliente.objects.filter(documento__in=documentos_en_vista).values('documento').annotate(total_refs=Count('id'))
        mapa_conteos = {item['documento']: item['total_refs'] for item in conteos_referencias}
        for doc_key in clientes_info_agrupada:
            clientes_info_agrupada[doc_key]['num_referencias'] = mapa_conteos.get(doc_key, 0)
    
    lista_para_paginar = sorted(list(clientes_info_agrupada.values()), key=lambda x: x['fecha_registro_grupo'], reverse=True)

    paginator = Paginator(lista_para_paginar, 15) # Muestra 15 grupos de clientes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form_nuevo_cliente = ClienteForm()

    context = {
        'page_obj': page_obj,
        'q': q,
        'is_grouped_view': True,
        'form_nuevo_cliente': form_nuevo_cliente
    }
    return render(request, 'core/clientes.html', context)

@login_required
def crear_cliente_view(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '¡Cliente creado exitosamente!')
                return redirect('clientes') # Redirige a la lista de clientes
            except IntegrityError: # Captura el error si la combinación documento-referencia ya existe
                # Esto es importante debido al unique_together = (('documento', 'referencia'),)
                # Si 'referencia' es opcional y se guarda como None o '', necesitas asegurar que la lógica de unicidad lo maneje bien.
                # O podrías necesitar una lógica más compleja si un cliente (documento) puede existir sin referencia inicialmente,
                # y luego se le añaden referencias.
                # Por ahora, asumimos que una referencia vacía/nula es válida para la unicidad si es la primera vez para ese documento.
                form.add_error(None, 'Error al guardar: Ya existe un cliente con el mismo documento y referencia (si aplica). Verifique los datos.')
        else:
            # Si el formulario no es válido, se mostrarán los errores en el template.
            # Para un modal, esto requeriría AJAX o recargar la página mostrando el modal con errores.
            # Por simplicidad inicial, si hay errores, la redirección no ocurrirá y el flujo normal del template (si no es modal AJAX) mostraría errores.
            # Si se usa AJAX, se devolvería un JSON con errores.
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ClienteForm()
    
    # Esta vista está pensada para ser llamada y renderizar su formulario dentro de un modal en la página de 'clientes'.
    # Por lo tanto, no renderiza una página completa por sí misma directamente, sino que el form se pasa al contexto de 'clientes.html'.
    # O, si se quiere una página dedicada (no modal), se haría: return render(request, 'core/crear_cliente.html', {'form': form})
    # Para el modal, la lógica de pasar el 'form' al contexto de 'clientes.html' se hará en la vista 'clientes'.
    # Si esta vista se llama vía AJAX, debería retornar JsonResponse.
    
    # Para un enfoque SIN AJAX y recarga de página con modal abierto (más simple inicialmente):
    # Si hay un error en POST, la vista 'clientes' necesitará saber que debe mostrar el modal con este form con errores.
    # Podríamos usar sesiones o un parámetro GET para indicar esto, o manejarlo completamente con AJAX.

    # Por ahora, esta vista está preparada para una redirección simple en caso de éxito POST.
    # El manejo de errores POST para un modal se abordará mejor con JavaScript/AJAX en el frontend.
    # Si no se usa AJAX, y hay un error, la página 'clientes' se recargaría y el modal no se mostraría con errores
    # a menos que la vista 'clientes' se modifique para manejar esto.
    return redirect('clientes') # Redirección temporal en caso de GET o error POST no manejado por AJAX

@login_required
@user_passes_test(es_admin)
def carga_clientes(request):
    """
    Vista para cargar clientes masivamente desde un archivo Excel o CSV
    """
    context = {
        'titulo': 'Carga masiva de clientes',
        'mensaje': '',
    }
    
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        extension = os.path.splitext(archivo.name)[1].lower()
        
        if extension not in ['.xlsx', '.csv']:
            messages.error(request, 'El archivo debe ser Excel (.xlsx) o CSV (.csv)')
            return render(request, 'core/carga_clientes.html', context)
        
        try:
            # Leer el archivo según su extensión
            if extension == '.xlsx':
                df = pd.read_excel(archivo)
            else:  # CSV
                df = pd.read_csv(archivo)
            
            # Procesar datos directamente con los nombres del modelo
            nuevos = 0
            actualizados = 0
            errores = [] # Para errores específicos de fila durante el procesamiento
            conversion_errores = [] # Para errores/avisos de conversión de datos

            # Renombrar columnas del DataFrame a minúsculas y quitar espacios/acentos para evitar errores
            df.columns = [c.strip().lower().replace('%', '').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').replace(' ', '_') for c in df.columns]
            
            campos_modelo = [
                'fecha_cesion','fecha_act','documento','referencia','tipo_documento','nombre_completo','ciudad',
                'dias_mora_originador','dias_mora_caso_sas','total_dias_mora','anios_mora','principal','deuda_principal_k',
                'intereses','tecnologia','seguro','otros_cargos','total_pagado','dcto_pago_contado_50','dcto_pago_contado_70_max_30',
                'deuda_total','telefono_celular','email','celular_1','celular_2','celular_3','direccion_1','direccion_2','direccion_3',
                'email_1','email_2','telefono_1','telefono_2'
            ]
            
            columnas_presentes_en_df = [c for c in campos_modelo if c in df.columns]
            if not columnas_presentes_en_df:
                messages.error(request, "El archivo no contiene ninguna de las columnas esperadas. Por favor, revisa el formato del archivo.")
                # Asegurarse que context['errores'] exista antes de añadir.
                if 'errores' not in context:
                    context['errores'] = []
                context['errores'].append("Formato de archivo incorrecto: no se encontraron columnas de datos válidas.")
                return render(request, 'core/carga_clientes.html', context)

            df_procesado = df[columnas_presentes_en_df].copy()

            campos_monetarios_a_entero = ['principal', 'intereses', 'tecnologia', 'seguro', 'otros_cargos', 'total_pagado']
            campo_decimal_grande = 'deuda_total'
            LIMITE_ENTERO_GRANDE = 2147483647

            def limpiar_valor_monetario(valor_original, campo_nombre, idx, es_decimal_field=False):
                if pd.isna(valor_original) or str(valor_original).strip().lower() in ('-', '', 'nan', 'none'):
                    return Decimal('0.00') if es_decimal_field else 0
                
                val_str = str(valor_original).replace('$', '').strip()
                
                if '.' in val_str and ',' in val_str:
                    if val_str.rfind('.') < val_str.rfind(','):
                        val_str = val_str.replace('.', '').replace(',', '.')
                elif ',' in val_str:
                    val_str = val_str.replace(',', '.')
                
                try:
                    valor_float = float(val_str)
                    if es_decimal_field:
                        return Decimal(str(valor_float))
                    else:
                        valor_redondeado = int(round(valor_float))
                        if abs(valor_redondeado) > LIMITE_ENTERO_GRANDE:
                            conversion_errores.append(f"Advertencia Fila {idx + 2}, Campo '{campo_nombre}': Valor '{valor_original}' ({valor_redondeado}) excede límite. Se usará {'el límite.' if LIMITE_ENTERO_GRANDE else '0'}")
                            return LIMITE_ENTERO_GRANDE if valor_redondeado > 0 else -LIMITE_ENTERO_GRANDE
                        return valor_redondeado
                except ValueError:
                    conversion_errores.append(f"Advertencia Fila {idx + 2}, Campo '{campo_nombre}': No se pudo convertir '{valor_original}' a número. Se usará 0.")
                    return Decimal('0.00') if es_decimal_field else 0

            for campo in campos_monetarios_a_entero:
                if campo in df_procesado.columns:
                    df_procesado[campo] = [limpiar_valor_monetario(val, campo, idx, es_decimal_field=False) for idx, val in enumerate(df_procesado[campo])]
            
            if campo_decimal_grande in df_procesado.columns:
                 df_procesado[campo_decimal_grande] = [limpiar_valor_monetario(val, campo_decimal_grande, idx, es_decimal_field=True) for idx, val in enumerate(df_procesado[campo_decimal_grande])]

            campos_numericos_simples = ['dias_mora_originador','dias_mora_caso_sas','total_dias_mora','anios_mora']
            for campo in campos_numericos_simples:
                if campo in df_procesado.columns:
                    df_procesado[campo] = pd.to_numeric(df_procesado[campo], errors='coerce').fillna(0).astype(int)
            
            campos_texto_a_numero_opcional = ['celular_1','celular_2','celular_3','telefono_celular','telefono_1','telefono_2']
            for campo in campos_texto_a_numero_opcional:
                 df_procesado[campo] = df_procesado[campo].astype(str).str.replace(r'[^\d\+]', '', regex=True)
                 df_procesado[campo] = df_procesado[campo].replace(r'^\+?$', None, regex=True)

            for campo_fecha in ['fecha_cesion', 'fecha_act']:
                if campo_fecha in df_procesado.columns:
                    df_procesado[campo_fecha] = pd.to_datetime(df_procesado[campo_fecha], format='%d/%m/%Y', errors='coerce')

            registros = df_procesado.to_dict('records')
            
            print(f"[DEBUG] Iniciando procesamiento de {len(registros)} registros del archivo.")

            for idx, registro_original in enumerate(registros):
                registro = registro_original.copy()
                documento = str(registro.get('documento', '')).strip()
                referencia_actual = str(registro.get('referencia', '')).strip()
                nombre = str(registro.get('nombre_completo', '')).strip()

                if not documento or not nombre:
                    errores.append(f"Fila {idx + 2}: Documento ('{documento}') y/o nombre ('{nombre}') son obligatorios y no pueden estar vacíos.")
                    continue
                
                defaults_data = {}
                for k, v in registro.items():
                    if k not in ['documento', 'referencia']:
                        if pd.isna(v):
                            defaults_data[k] = None
                        else:
                            defaults_data[k] = v
                
                referencia_para_db = referencia_actual if referencia_actual else None

                print(f"[DEBUG] Fila {idx + 2}: Intentando update_or_create para Documento='{documento}', Referencia='{referencia_para_db}'")

                try:
                    cliente, created = Cliente.objects.update_or_create(
                        documento=documento,
                        referencia=referencia_para_db, 
                        defaults=defaults_data
                    )
                    if created:
                        nuevos += 1
                    else:
                        actualizados += 1
                except IntegrityError as ie:
                    errores.append(f"Fila {idx + 2} (Doc: {documento}, Ref: {referencia_actual}): Error de integridad - {str(ie)}.")
                except Exception as e:
                    errores.append(f"Fila {idx + 2} (Doc: {documento}, Ref: {referencia_actual}): Error al guardar - {str(e)}")
            
            context['resumen'] = {
                'nuevos': nuevos,
                'actualizados': actualizados,
                'duplicados': 0 
            }
            if errores:
                context.setdefault('errores', []).extend(errores)
                messages.warning(request, f'Carga completada. {nuevos} nuevos, {actualizados} actualizados. Se encontraron {len(errores)} errores.')
            if conversion_errores:
                context.setdefault('advertencias_conversion', []).extend(conversion_errores)

            if not errores and not conversion_errores:
                messages.success(request, f'Carga exitosa: {nuevos} nuevos, {actualizados} actualizados.')
            elif not errores and conversion_errores:
                 messages.info(request, f'Carga completada con advertencias: {nuevos} nuevos, {actualizados} actualizados. {len(conversion_errores)} advertencias.')
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
    
    # Inicializar context aquí si no se entró al POST, para evitar UnboundLocalError
    if 'resumen' not in context:
        context['resumen'] = {}
    if 'errores' not in context:
        context['errores'] = []
        
    return render(request, 'core/carga_clientes.html', context)

@login_required
@user_passes_test(es_admin)
def detalle_cliente(request, documento_cliente):
    """Vista para ver detalles de un cliente (agrupado por documento) y sus referencias."""
    
    # Obtener todas las referencias para el documento dado, ordenadas por fecha de registro o como prefieras
    referencias_cliente = Cliente.objects.filter(documento=documento_cliente).order_by('-fecha_registro', 'referencia')
    
    if not referencias_cliente.exists():
        raise Http404(f"No se encontraron clientes con el documento {documento_cliente}")
    
    # Usar la primera referencia (o la más reciente según el orden) como la "principal" para datos generales
    cliente_representativo = referencias_cliente.first()
    
    # Calcular totales financieros sumando los campos de todas las referencias
    # Asegúrate de que los campos sean numéricos y maneja posibles None con Coalesce si es necesario
    # from django.db.models.functions import Coalesce # Importar si se usa Coalesce
    
    totales_financieros = referencias_cliente.aggregate(
        total_principal=Sum('principal'), # Asumiendo que 'principal' es un campo numérico en el modelo Cliente
        total_deuda_principal_k=Sum('deuda_principal_k'),
        total_deuda_total=Sum('deuda_total')
        # Agrega aquí otros campos financieros que necesites sumar
    )
    
    context = {
        'cliente_representativo': cliente_representativo, # Para mostrar info general del cliente
        'referencias_cliente': referencias_cliente,       # Lista de todas las referencias para la pestaña
        'documento_cliente': documento_cliente,           # Para mostrar en la plantilla o usar en enlaces
        'totales_financieros': totales_financieros,       # Diccionario con los totales
        'is_detail_view': True                            # Para la plantilla, si es necesario diferenciar
    }
    
    # ----- Lógica de POST (Actualización) -----
    # Por ahora, deshabilitaremos la edición directa desde esta vista agrupada para simplificar.
    # La edición podría manejarse a nivel de referencia individual o con una estrategia definida.
    # Si se decide mantener la edición, se necesitará una lógica cuidadosa para determinar
    # qué referencia(s) actualizar.
    
    # if request.method == 'POST':
    #     # ... lógica de actualización compleja ...
    #     # Por ejemplo, si se edita el nombre, ¿se actualiza en todas las referencias?
    #     # ¿O solo en la 'cliente_representativo'?
    #     # messages.warning(request, "La edición de datos agrupados aún no está implementada.")
    #     pass # No hacer nada en POST por ahora
        
    return render(request, 'core/detalle_cliente.html', context)

@login_required
def solo_admin(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.groups.filter(name="Administrador").exists():
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def perfil_usuario(request):
    user = request.user
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        errores = []
        if nombre:
            user.first_name = nombre
        if password1 or password2:
            if password1 != password2:
                errores.append('Las contraseñas no coinciden.')
            elif len(password1) < 6:
                errores.append('La nueva contraseña debe tener al menos 6 caracteres.')
            else:
                user.set_password(password1)
        if not errores:
            user.save()
            if password1:
                update_session_auth_hash(request, user)
                messages.success(request, 'Datos y contraseña actualizados correctamente.')
            else:
                messages.success(request, 'Datos actualizados correctamente.')
            return redirect('perfil')
        else:
            for err in errores:
                messages.error(request, err)
    return render(request, 'core/perfil.html', {'user': user})



def es_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact='Administrador').exists()

@user_passes_test(es_admin)
def admin_usuarios(request):
    q = request.GET.get('q', '').strip()
    grupo_filtro = request.GET.get('grupo', '').strip()
    usuarios = User.objects.all().order_by('username')
    grupos = Group.objects.all().order_by('name')

    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )
    if grupo_filtro:
        usuarios = usuarios.filter(groups__name__iexact=grupo_filtro)

    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        grupo_id = request.POST.get('grupo_id')
        accion = request.POST.get('accion')
        if accion == 'toggle_activo' and user_id:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f'Usuario {"activado" if user.is_active else "desactivado"} correctamente.')
            return redirect(request.path + f'?q={q}&grupo={grupo_filtro}&page={page_number}')
        if user_id and grupo_id:
            user = User.objects.get(id=user_id)
            grupo = Group.objects.get(id=grupo_id)
            user.groups.clear()
            user.groups.add(grupo)
            return redirect(request.path + f'?q={q}&grupo={grupo_filtro}&page={page_number}')

    return render(request, 'core/admin_usuarios.html', {
        'page_obj': page_obj,
        'grupos': grupos,
        'q': q,
        'grupo_filtro': grupo_filtro,
    })

@login_required
@user_passes_test(es_admin)
def detalle_usuario(request, user_id):
    """
    Vista para mostrar el detalle de un usuario y permitir su activación/desactivación
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'El usuario solicitado no existe.')
        return redirect('admin_usuarios')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'toggle_activo':
            user.is_active = not user.is_active
            user.save()
            estado = 'activado' if user.is_active else 'desactivado'
            messages.success(request, f'Usuario {user.username} {estado} correctamente.')
            return redirect('admin_usuarios')

    return render(request, 'core/detalle_usuario.html', {
        'usuario': user,
    })