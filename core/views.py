from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count
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

from .models import *
from .forms import EmailAuthenticationForm

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
@user_passes_test(es_admin)
def clientes(request):
    q = request.GET.get('q', '').strip()
    clientes = Cliente.objects.all().order_by('-fecha_registro')
    if q:
        clientes = clientes.filter(
            Q(nombre_completo__icontains=q) |
            Q(documento__icontains=q) |
            Q(referencia__icontains=q)
        )
    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/clientes.html', {'page_obj': page_obj})

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
                
            # Depuración simple
            print("Archivo cargado con éxito. Columnas detectadas:", df.columns.tolist())
            
            # Crear diccionario de mapeo directo entre columnas Excel y campos del modelo
            # Estos son los mapeos exactos que se usarán
            mapeo_directo = {
                'DOCUMENTO': 'documento',
                'NOMBRE COMPLETO': 'nombre_completo',
                'REFERENCIA': 'referencia',
                'CIUDAD': 'ciudad',
                'CC': 'tipo_documento',
                'DIAS MORA ORIGINADOR': 'dias_mora_originador',
                'DIAS MORA CASO SAS': 'dias_mora_caso_sas',  
                'TOTAL DIAS MORA': 'total_dias_mora',
                'AÑOS MORA': 'anios_mora',
                'PRINCIPAL': 'principal',
                'DEUDA PRINCIPAL K': 'deuda_principal_k',
                'DEUDA TOTAL': 'deuda_total',
                'INTERESES': 'intereses',
                'TECNOLOGIA': 'tecnologia',
                'SEGURO': 'seguro',
                'OTROS CARGOS': 'otros_cargos',
                'TOTAL PAGADO': 'total_pagado',
                'DCTO PAGO CONTADO 50%': 'dcto_pago_contado_50',
                'DCTO PAGO CONTADO 70% MAX. 30%': 'dcto_pago_contado_70_max_30',
                'TELEFONO 1': 'telefono_1',
                'TELEFONO 2': 'telefono_2',
                'TELEFONO 3': 'telefono_3',
                'TELEFONO CELULAR': 'celular_1',
                'CELULAR_1': 'celular_1',
                'CELULAR_2': 'celular_2',
                'CELULAR_3': 'celular_3',
                'CELULAR_4': 'celular_4',
                'CELULAR_5': 'celular_5',
                'EMAIL': 'email',
                'EMAIL 1': 'email_1',
                'EMAIL 2': 'email_2',
                'EMAIL 3': 'email_3',
                'DIRECCION 1': 'direccion_1',
                'DIRECCION 2': 'direccion_2',
                'DIRECCION 3': 'direccion_3',
                'FECHA CESION': 'fecha_cesion',
                'FECHA ACT': 'fecha_act'
            }
            
            # Procesar datos
            nuevos = 0
            actualizados = 0
            errores = []
            
            # Crear un nuevo DataFrame para almacenar los datos procesados
            df_procesado = pd.DataFrame()
            
            # Procesar cada columna usando el mapeo directo
            for col_excel, campo_modelo in mapeo_directo.items():
                if col_excel in df.columns:
                    # Copiar la columna con el nuevo nombre
                    df_procesado[campo_modelo] = df[col_excel].copy()
                    print(f"Mapeando: '{col_excel}' -> '{campo_modelo}'")
            
            # Procesamiento específico para ciertos tipos de campos
            # Limpiar valores monetarios
            campos_monetarios = ['principal', 'deuda_principal_k', 'deuda_total', 'intereses', 'tecnologia', 
                               'seguro', 'otros_cargos', 'total_pagado', 'dcto_pago_contado_50', 'dcto_pago_contado_70_max_30']
            
            for campo in campos_monetarios:
                if campo in df_procesado.columns:
                    # Convertir a string para poder realizar operaciones de texto
                    df_procesado[campo] = df_procesado[campo].astype(str)
                    # Eliminar símbolos y dar formato
                    df_procesado[campo] = df_procesado[campo].str.replace('$', '', regex=False)
                    df_procesado[campo] = df_procesado[campo].str.replace(' ', '', regex=False)
                    # Manejo especial para DEUDA TOTAL
                    if campo == 'deuda_total':
                        # Intentar mantener el formato decimal original
                        df_procesado[campo] = df_procesado[campo].apply(lambda x: 
                            float(x.replace('.', '').replace(',', '.')) if isinstance(x, str) else float(x))
                    else:
                        # Para otros campos monetarios, convertir a entero
                        try:
                            df_procesado[campo] = df_procesado[campo].apply(lambda x: 
                                int(float(x.replace('.', '').replace(',', '.'))) if isinstance(x, str) else int(float(x)))
                        except Exception as e:
                            print(f"Error al procesar campo monetario {campo}: {str(e)}")
            
            # Procesar campos de fecha
            campos_fecha = ['fecha_cesion', 'fecha_act']
            for campo in campos_fecha:
                if campo in df_procesado.columns:
                    try:
                        df_procesado[campo] = pd.to_datetime(df_procesado[campo], format='%d/%m/%Y', errors='coerce')
                    except Exception as e:
                        print(f"Error al convertir fecha {campo}: {str(e)}")
            
            # Procesar campos enteros
            campos_enteros = ['dias_mora_caso_sas', 'dias_mora_originador', 'total_dias_mora', 'anios_mora']
            for campo in campos_enteros:
                if campo in df_procesado.columns:
                    try:
                        df_procesado[campo] = df_procesado[campo].astype(str).str.replace(',', '.', regex=False)
                        df_procesado[campo] = pd.to_numeric(df_procesado[campo], errors='coerce')
                        df_procesado[campo] = df_procesado[campo].fillna(0).astype(int)
                    except Exception as e:
                        print(f"Error al convertir entero {campo}: {str(e)}")
            
            # Mostrar datos procesados
            print("\nDatos procesados:")
            print(df_procesado.head())
            
            # Convertir a registros para procesar
            registros = df_procesado.to_dict('records')
            print(f"Procesando {len(registros)} registros...")
            
            # Validar documento - campo obligatorio
            for idx, registro in enumerate(registros):
                if 'documento' not in registro or pd.isna(registro['documento']):
                    errores.append(f"Fila {idx + 2}: Falta el documento")
                    continue
                    
                # Preparar datos para crear o actualizar el cliente
                try:
                    documento = str(registro.get('documento', '')).strip()
                    nombre = str(registro.get('nombre_completo', '')).strip()
                    
                    # Validar datos mínimos
                    if not documento or not nombre:
                        errores.append(f"Fila {idx + 2}: Documento y nombre completo son obligatorios")
                        continue
                        
                    # Crear o actualizar cliente
                    cliente, created = Cliente.objects.update_or_create(
                        documento=documento,
                        defaults=registro
                    )
                    
                    if created:
                        nuevos += 1
                    else:
                        actualizados += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx + 2}: {str(e)}")

            # Preparar resumen para mostrar
            context['resumen'] = {
                'nuevos': nuevos,
                'actualizados': actualizados,
                'duplicados': duplicados
            }
            
            if errores:
                context['errores'] = errores
                messages.warning(request, f'Carga completada con {len(errores)} errores')
            else:
                messages.success(request, f'Carga exitosa: {nuevos} nuevos, {actualizados} actualizados')
                
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
    
    return render(request, 'core/carga_clientes.html', context)

@login_required
@user_passes_test(es_admin)
def detalle_cliente(request, cliente_id):
    """Vista para ver y editar detalles de un cliente"""
    # Usamos get_object_or_404 que automáticamente lanzará Http404 si el cliente no existe
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    context = {'cliente': cliente}
    
    if request.method == 'POST':
        # Obtener datos básicos del formulario
        nombre = request.POST.get('nombre_completo', '').strip()
        referencia = request.POST.get('referencia', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        estado = request.POST.get('estado', 'Activo').strip()
        
        # Información de contacto
        telefono_1 = request.POST.get('telefono_1', '').strip()
        telefono_2 = request.POST.get('telefono_2', '').strip()
        telefono_3 = request.POST.get('telefono_3', '').strip()
        celular_1 = request.POST.get('celular_1', '').strip()
        celular_2 = request.POST.get('celular_2', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Información financiera
        dias_mora_caso_sas = request.POST.get('dias_mora_caso_sas', 0)
        dias_mora_originador = request.POST.get('dias_mora_originador', 0)
        total_dias_mora = request.POST.get('total_dias_mora', 0)
        anios_mora = request.POST.get('anios_mora', 0)
        principal = request.POST.get('principal', 0)
        deuda_principal_k = request.POST.get('deuda_principal_k', 0)
        deuda_total = request.POST.get('deuda_total', 0)
        
        # Direcciones
        direccion_1 = request.POST.get('direccion_1', '').strip()
        direccion_2 = request.POST.get('direccion_2', '').strip()
        direccion_3 = request.POST.get('direccion_3', '').strip()
        
        # Validar datos
        errores = []
        if not nombre:
            errores.append('El nombre completo es obligatorio')
        
        if not errores:
            # Actualizar información básica
            cliente.nombre_completo = nombre
            cliente.referencia = referencia
            cliente.ciudad = ciudad
            cliente.estado = estado
            
            # Actualizar información de contacto
            cliente.telefono_1 = telefono_1
            cliente.telefono_2 = telefono_2
            cliente.telefono_3 = telefono_3
            cliente.celular_1 = celular_1
            cliente.celular_2 = celular_2
            cliente.email = email
            
            # Actualizar información financiera - manejo seguro de conversiones
            try:
                cliente.dias_mora_caso_sas = int(dias_mora_caso_sas) if dias_mora_caso_sas and dias_mora_caso_sas.strip() else cliente.dias_mora_caso_sas
            except (ValueError, TypeError):
                # Mantener el valor original si hay error
                pass
                
            try:
                cliente.dias_mora_originador = int(dias_mora_originador) if dias_mora_originador and dias_mora_originador.strip() else cliente.dias_mora_originador
            except (ValueError, TypeError):
                pass
                
            try:
                cliente.total_dias_mora = int(total_dias_mora) if total_dias_mora and total_dias_mora.strip() else cliente.total_dias_mora
            except (ValueError, TypeError):
                pass
                
            try:
                cliente.anios_mora = int(anios_mora) if anios_mora and anios_mora.strip() else cliente.anios_mora
            except (ValueError, TypeError):
                pass
            
            try:
                cliente.principal = float(principal) if principal and principal.strip() else cliente.principal
            except (ValueError, TypeError):
                pass
                
            try:
                cliente.deuda_principal_k = float(deuda_principal_k) if deuda_principal_k and deuda_principal_k.strip() else cliente.deuda_principal_k
            except (ValueError, TypeError):
                pass
                
            try:
                cliente.deuda_total = float(deuda_total) if deuda_total and deuda_total.strip() else cliente.deuda_total
            except (ValueError, TypeError):
                pass
            
            # Actualizar direcciones
            cliente.direccion_1 = direccion_1
            cliente.direccion_2 = direccion_2
            cliente.direccion_3 = direccion_3
            
            # Guardar cambios
            cliente.save()
            
            messages.success(request, 'Cliente actualizado correctamente')
            context['mensaje'] = 'Cliente actualizado correctamente'
        else:
            context['errores'] = errores
    
    return render(request, 'core/detalle_cliente.html', context)

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