from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from .utils import enviar_correo_prueba
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count, Sum, Max, F, Value, functions
from django.db.models.functions import Concat
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
import json
import pandas as pd
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db import IntegrityError
from .models import Cliente, User, LoginUser, Gestion
from .forms import EmailAuthenticationForm, ClienteForm, GestionForm
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

@login_required
def dashboard(request):
    from django.db.models import Sum, Count, Q, F
    from datetime import datetime, timedelta
    
    # Obtener la fecha actual y el primer día del mes
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # 1. Métricas de Clientes
    # Clientes únicos por documento
    total_clientes_unicos = Cliente.objects.values('documento').distinct().count()
    # Total de registros en el modelo Cliente (productos)
    total_productos = Cliente.objects.count()
    
    # Clientes con acuerdo de pago activo (últimos 30 días o futuros)
    fecha_limite = hoy - timedelta(days=30)
    print(f"\n[DEBUG] Buscando acuerdos desde: {fecha_limite}")
    
    # Consulta alternativa usando subconsulta para evitar problemas de relaciones
    from django.db.models import Exists, OuterRef
    
    # Primero, obtener los IDs de las gestiones con acuerdo reciente
    gestiones_recientes = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_acuerdo__isnull=False,
        fecha_acuerdo__gte=fecha_limite
    ).values_list('cliente_id', flat=True).distinct()
    
    # Luego, contar clientes únicos con esas gestiones
    clientes_con_acuerdo = Cliente.objects.filter(
        id__in=gestiones_recientes
    ).count()
    
    # Depuración detallada
    print(f"[DEBUG] Número de clientes con acuerdo (método alternativo): {clientes_con_acuerdo}")
    
    # Información adicional para depuración
    gestiones_ejemplo = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_acuerdo__isnull=False
    ).select_related('cliente').order_by('-fecha_acuerdo')[:5]
    
    print("\n[DEBUG] Ejemplo de gestiones con acuerdo:")
    for g in gestiones_ejemplo:
        cliente_info = f"{g.cliente.nombre_completo} (ID: {g.cliente_id})" if g.cliente else "Sin cliente"
        print(f"  - Gestión ID: {g.id}, Fecha: {g.fecha_acuerdo}, Cliente: {cliente_info}")
    
    # Si no hay acuerdos recientes, mostrar un mensaje de advertencia
    if clientes_con_acuerdo == 0:
        print("\n[ADVERTENCIA] No se encontraron clientes con acuerdos recientes.")
        print("[ADVERTENCIA] Verificar que existan gestiones con 'acuerdo_pago_realizado=True' y 'fecha_acuerdo' válida.")
    clientes_activos = Cliente.objects.filter(estado='activo').values('documento').distinct().count()
    clientes_nuevos_este_mes = Cliente.objects.filter(
        fecha_registro__month=hoy.month, 
        fecha_registro__year=hoy.year
    ).values('documento').distinct().count()
    
    # 2. Métricas de Cartera
    cartera_total = Cliente.objects.aggregate(total=Sum('deuda_total'))['total'] or 0
    cartera_vencida = Cliente.objects.filter(estado='en_mora').aggregate(total=Sum('deuda_total'))['total'] or 0
    
    # Calcular porcentaje de mora
    porcentaje_mora = (cartera_vencida / cartera_total * 100) if cartera_total > 0 else 0
    
    # 3. Total de compromisos de pago
    total_compromisos = Gestion.objects.filter(acuerdo_pago_realizado=True).count()
    
    # 4. Pagos del mes actual (solo cuando se registra un pago)
    pagos_este_mes = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_pago_efectivo__isnull=False,  # Solo pagos registrados
        fecha_pago_efectivo__month=hoy.month,
        fecha_pago_efectivo__year=hoy.year
    ).count()
    
    # 5. Estados de los compromisos de pago
    # Usamos fecha_acuerdo + 30 días como fecha de vencimiento temporal
    compromisos_vigentes = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_acuerdo__gte=hoy - timedelta(days=30),  # Compromisos de los últimos 30 días
        fecha_pago_efectivo__isnull=True  # Que no tengan pago registrado
    ).count()
    
    compromisos_vencidos = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_acuerdo__lt=hoy - timedelta(days=30),  # Compromisos con más de 30 días
        fecha_pago_efectivo__isnull=True  # Que no tengan pago registrado
    ).count()
    
    # Datos para el gráfico de compromisos
    total_compromisos_grafico = compromisos_vigentes + compromisos_vencidos
    porcentaje_vigentes = (compromisos_vigentes / total_compromisos_grafico * 100) if total_compromisos_grafico > 0 else 0
    porcentaje_vencidos = (compromisos_vencidos / total_compromisos_grafico * 100) if total_compromisos_grafico > 0 else 0
    
    compromisos_data = {
        'labels': ['Vigentes', 'Vencidos'],
        'datos': [compromisos_vigentes, compromisos_vencidos],
        'porcentajes': [round(porcentaje_vigentes, 1), round(porcentaje_vencidos, 1)],
        'colores': ['#28a745', '#dc3545']
    }
    
    # 5. Datos para el gráfico de distribución de cartera por estado
    distribucion_cartera = Cliente.objects.values('estado').annotate(
        total=Sum('deuda_total'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Preparar datos para el gráfico
    etiquetas_distribucion = []
    valores_distribucion = []
    colores_grafico = []
    cantidades = []
    
    # Definir colores para cada estado
    colores = {
        'activo': 'rgba(40, 167, 69, 0.8)',    # Verde
        'en_mora': 'rgba(220, 53, 69, 0.8)',   # Rojo
        'incobrable': 'rgba(108, 117, 125, 0.8)', # Gris
        'pagado': 'rgba(23, 162, 184, 0.8)',    # Celeste
        'juridico': 'rgba(111, 66, 193, 0.8)'   # Morado
    }
    
    for item in distribucion_cartera:
        if item['estado'] in colores and item['total'] is not None and float(item['total']) > 0:
            etiquetas_distribucion.append(dict(Cliente.ESTADO_CHOICES).get(item['estado'], item['estado']))
            valores_distribucion.append(float(item['total']))
            colores_grafico.append(colores[item['estado']])
            cantidades.append(item['cantidades'])
    
    # 6. Próximos Seguimientos (para el calendario)
    proximos_seguimientos = Gestion.objects.filter(
        fecha_proximo_seguimiento__gte=hoy
    ).order_by('fecha_proximo_seguimiento', 'hora_proximo_seguimiento')[:10]
    
    # 7. Actividad Reciente
    actividad_reciente = Gestion.objects.select_related('cliente', 'usuario_gestion').order_by('-fecha_hora_gestion')[:10]
    
    # 8. Datos para el gráfico de distribución de cartera
    distribucion_cartera_data = {
        'labels': etiquetas_distribucion,
        'datos': valores_distribucion,
        'colores': colores_grafico,
        'cantidades': cantidades
    }
    
    # 9. Resumen de Gestiones por Tipo
    resumen_gestiones = Gestion.objects.values('tipo_gestion_n1').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # 10. Próximos Vencimientos (para la tabla)
    # Usamos fecha_act como aproximación para próximos vencimientos
    proximos_vencimientos = Cliente.objects.filter(
        fecha_act__gte=hoy,
        fecha_act__lte=hoy + timedelta(days=7)
    ).order_by('fecha_act')[:10]
    
    # 11. Datos para el gráfico de cobranza mensual (últimos 12 meses)
    fecha_hace_12_meses = hoy - timedelta(days=365)
    cobranza_mensual = Gestion.objects.filter(
        acuerdo_pago_realizado=True,
        fecha_acuerdo__gte=fecha_hace_12_meses
    ).extra(
        select={'mes': "to_char(fecha_acuerdo, 'YYYY-MM')"}
    ).values('mes').annotate(
        total=Sum('monto_acuerdo')
    ).order_by('mes')
    
    # Preparar datos para el gráfico de cobranza
    meses_cobranza = []
    valores_cobranza = []
    
    for mes in range(12):
        fecha = hoy.replace(day=1) - timedelta(days=30*mes)
        mes_str = fecha.strftime('%Y-%m')
        meses_cobranza.insert(0, fecha.strftime('%b %Y'))
        
        # Buscar si hay datos para este mes
        monto = next((item['total'] for item in cobranza_mensual if item['mes'] == mes_str), 0)
        valores_cobranza.insert(0, float(monto) if monto else 0)
    
    # Preparar el contexto para la plantilla
    context = {
        'hoy': hoy,
        'primer_dia_mes': primer_dia_mes,
        'hoy_str': hoy.strftime('%Y-%m-%d'),
        'total_clientes': total_clientes_unicos,  # Clientes únicos por documento
        'total_productos': total_productos,  # Total de registros en el modelo Cliente
        'clientes_con_acuerdo': clientes_con_acuerdo,
        'clientes_activos': clientes_activos,
        'clientes_nuevos_este_mes': clientes_nuevos_este_mes,
        'cartera_total': cartera_total,
        'cartera_vencida': cartera_vencida,
        'porcentaje_mora': porcentaje_mora,
        'pagos_este_mes': pagos_este_mes,
        'total_compromisos': total_compromisos,  # Total de compromisos de pago
        'compromisos_vigentes': compromisos_vigentes,
        'compromisos_vencidos': compromisos_vencidos,
        'compromisos_data': compromisos_data,
        'proximos_seguimientos': proximos_seguimientos,
        'actividad_reciente': actividad_reciente,
        'distribucion_cartera': distribucion_cartera_data,
        'resumen_gestiones': resumen_gestiones,
        'proximos_vencimientos': proximos_vencimientos,
        'cobranza_mensual': list(cobranza_mensual),
        'meses': [f"{mes['mes']}" for mes in cobranza_mensual],
        'solicitudes_por_mes': [float(mes['total']) for mes in cobranza_mensual],
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'usuarios_inactivos': User.objects.filter(is_active=False).count(),
    }
    
    return render(request, 'core/dashboard.html', context)

def inicio(request):
    return render(request, 'core/inicio.html')

def es_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact='Administrador').exists()

@login_required
def clientes(request):
    # Obtener parámetros de filtro individuales
    filtro_documento = request.GET.get('documento', '').strip()
    filtro_nombre = request.GET.get('nombre', '').strip()
    filtro_telefono = request.GET.get('telefono', '').strip()
    filtro_referencia = request.GET.get('referencia', '').strip()

    # Queryset base, ordenado para obtener el representante más reciente del grupo
    clientes_qs = Cliente.objects.all().order_by('documento', '-fecha_registro')

    # Construir filtros dinámicamente
    filtros = Q()
    if filtro_documento:
        filtros &= Q(documento__icontains=filtro_documento)
    if filtro_nombre:
        filtros &= Q(nombre_completo__icontains=filtro_nombre)
    if filtro_telefono:
        # Asumiendo que quieres buscar en varios campos de teléfono
        filtros &= (Q(telefono_celular__icontains=filtro_telefono) |
                    Q(celular_1__icontains=filtro_telefono) |
                    Q(celular_2__icontains=filtro_telefono) |
                    Q(celular_3__icontains=filtro_telefono) |
                    Q(telefono_1__icontains=filtro_telefono) |
                    Q(telefono_2__icontains=filtro_telefono))
    if filtro_referencia:
        filtros &= Q(referencia__icontains=filtro_referencia)
    
    if filtros: # Solo aplicar filtros si hay alguno
        clientes_qs = clientes_qs.filter(filtros)

    clientes_info_agrupada = {}
    documentos_coincidentes = set(clientes_qs.values_list('documento', flat=True))

    if documentos_coincidentes:
        representantes_qs = Cliente.objects.filter(documento__in=documentos_coincidentes)\
                                      .order_by('documento', '-fecha_registro')\
                                      .distinct('documento')

        for rep in representantes_qs:
            clientes_info_agrupada[rep.documento] = {
                'documento': rep.documento,
                'nombre_completo': rep.nombre_completo,
                'email': rep.email, 
                'deuda_total': rep.deuda_total,
                'total_dias_mora': rep.total_dias_mora,
                'fecha_cesion': rep.fecha_cesion,
                'num_referencias': 0, 
                'fecha_registro_grupo': rep.fecha_registro
            }

        conteos_referencias = Cliente.objects.filter(documento__in=documentos_coincidentes)\
                                        .values('documento')\
                                        .annotate(total_refs=Count('id'))
        mapa_conteos = {item['documento']: item['total_refs'] for item in conteos_referencias}
        
        for doc_key in clientes_info_agrupada:
            clientes_info_agrupada[doc_key]['num_referencias'] = mapa_conteos.get(doc_key, 0)

    lista_para_paginar = sorted(list(clientes_info_agrupada.values()), key=lambda x: x['fecha_registro_grupo'], reverse=True)

    paginator = Paginator(lista_para_paginar, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form_nuevo_cliente = ClienteForm() 

    context = {
        'page_obj': page_obj,
        'form_nuevo_cliente': form_nuevo_cliente,
        'filtro_documento': filtro_documento,
        'filtro_nombre': filtro_nombre,
        'filtro_telefono': filtro_telefono,
        'filtro_referencia': filtro_referencia,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/_tabla_clientes_parcial.html', context)
    
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
def agregar_gestion_cliente(request, documento_cliente):
    cliente = get_object_or_404(Cliente, documento=documento_cliente)
    if request.method == 'POST':
        form = GestionForm(request.POST)
        if form.is_valid():
            gestion = form.save(commit=False)
            gestion.cliente = cliente
            gestion.usuario_gestion = request.user # Asignar el usuario logueado
            gestion.save()
            messages.success(request, 'Gestión agregada exitosamente.')
            return redirect('detalle_cliente', documento_cliente=documento_cliente)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = GestionForm(initial={'cliente': cliente})
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo_pagina': 'Agregar Nueva Gestión'
    }
    return render(request, 'core/agregar_gestion.html', context)

@login_required
def lista_gestiones(request):
    # Obtener parámetros de filtro
    cliente_filtro = request.GET.get('cliente', '')
    asesor_filtro = request.GET.get('asesor', '')
    tipo_gestion_filtro = request.GET.get('tipo_gestion', '')
    estado_contacto_filtro = request.GET.get('estado_contacto', '')
    
    # Iniciar consulta base
    gestiones_list = Gestion.objects.select_related('cliente', 'usuario_gestion').all()
    
    # Aplicar filtros si se proporcionan
    if cliente_filtro:
        gestiones_list = gestiones_list.filter(
            Q(cliente__nombre_completo__icontains=cliente_filtro) | 
            Q(cliente__documento__icontains=cliente_filtro)
        )
    
    if asesor_filtro:
        gestiones_list = gestiones_list.filter(usuario_gestion_id=asesor_filtro)
    
    if tipo_gestion_filtro:
        gestiones_list = gestiones_list.filter(
            Q(tipo_gestion_n1__icontains=tipo_gestion_filtro) | 
            Q(tipo_gestion_n2__icontains=tipo_gestion_filtro) | 
            Q(tipo_gestion_n3__icontains=tipo_gestion_filtro)
        )
    
    if estado_contacto_filtro:
        gestiones_list = gestiones_list.filter(estado_contacto=estado_contacto_filtro)
    
    # Ordenar por fecha descendente
    gestiones_list = gestiones_list.order_by('-fecha_hora_gestion')
    
    # Paginación
    paginator = Paginator(gestiones_list, 10) # Mostrar 10 gestiones por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener todos los asesores para el filtro
    User = get_user_model()
    asesores = User.objects.filter(is_active=True).order_by('first_name')
    
    context = {
        'page_obj': page_obj,
        'cliente': cliente_filtro,
        'asesor': asesor_filtro,
        'tipo_gestion': tipo_gestion_filtro,
        'estado_contacto': estado_contacto_filtro,
        'asesores': asesores,
        'total_gestiones': gestiones_list.count()
    }
    
    # Si es una solicitud AJAX, renderizar solo la tabla parcial
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'core/_tabla_gestiones_parcial.html', context)
    
    # De lo contrario, renderizar la página completa
    return render(request, 'core/lista_gestiones.html', context)

@login_required
@user_passes_test(es_admin)
def acuerdos_pago(request):
    # Filtros para acuerdos de pago
    documento = request.GET.get('documento', '')
    nombre = request.GET.get('nombre', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    estado = request.GET.get('estado', '')
    
    # Consulta base: solo gestiones con acuerdo de pago
    acuerdos_list = Gestion.objects.select_related('cliente', 'usuario_gestion')\
                          .filter(acuerdo_pago_realizado=True)\
                          .order_by('-fecha_acuerdo')
    
    # Aplicar filtros si están presentes
    if documento:
        acuerdos_list = acuerdos_list.filter(cliente__documento__icontains=documento)
    if nombre:
        acuerdos_list = acuerdos_list.filter(cliente__nombre_completo__icontains=nombre)
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            acuerdos_list = acuerdos_list.filter(fecha_acuerdo__gte=fecha_desde_obj)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            acuerdos_list = acuerdos_list.filter(fecha_acuerdo__lte=fecha_hasta_obj)
        except ValueError:
            pass
    if estado:
        # Estado personalizado: 'vigente' o 'vencido'
        today = datetime.now().date()
        if estado == 'vigente':
            acuerdos_list = acuerdos_list.filter(fecha_acuerdo__gte=today)
        elif estado == 'vencido':
            acuerdos_list = acuerdos_list.filter(fecha_acuerdo__lt=today)
    
    # Paginación
    paginator = Paginator(acuerdos_list, 25)  # 25 acuerdos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Preparar contexto
    context = {
        'page_obj': page_obj,
        'titulo_pagina': 'Acuerdos de Pago',
        'total_acuerdos': acuerdos_list.count(),
        'filtros': {
            'documento': documento,
            'nombre': nombre,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'estado': estado
        },
        'today': datetime.now().date()
    }
    
    # Si es una solicitud AJAX, devolver solo la tabla
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'core/partials/tabla_acuerdos.html', context)
    
    return render(request, 'core/acuerdos_pago.html', context)

@login_required
@user_passes_test(es_admin)
def seguimientos(request):
    # Filtros para seguimientos
    documento = request.GET.get('documento', '')
    nombre = request.GET.get('nombre', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    usuario = request.GET.get('usuario', '')
    
    # Consulta base: solo gestiones con seguimiento requerido
    seguimientos_list = Gestion.objects.select_related('cliente', 'usuario_gestion')\
                              .filter(seguimiento_requerido=True)\
                              .order_by('fecha_proximo_seguimiento')
    
    # Aplicar filtros si están presentes
    if documento:
        seguimientos_list = seguimientos_list.filter(cliente__documento__icontains=documento)
    if nombre:
        seguimientos_list = seguimientos_list.filter(cliente__nombre_completo__icontains=nombre)
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            seguimientos_list = seguimientos_list.filter(fecha_proximo_seguimiento__gte=fecha_desde_obj)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            seguimientos_list = seguimientos_list.filter(fecha_proximo_seguimiento__lte=fecha_hasta_obj)
        except ValueError:
            pass
    if usuario:
        seguimientos_list = seguimientos_list.filter(usuario_gestion__username__icontains=usuario)
    
    # Paginación
    paginator = Paginator(seguimientos_list, 25)  # 25 seguimientos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Preparar contexto
    today = datetime.now().date()
    context = {
        'page_obj': page_obj,
        'titulo_pagina': 'Seguimientos Pendientes',
        'total_seguimientos': seguimientos_list.count(),
        'filtros': {
            'documento': documento,
            'nombre': nombre,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'usuario': usuario
        },
        'today': today,
        'usuarios': User.objects.filter(is_active=True).order_by('username')
    }
    
    # Si es una solicitud AJAX, devolver solo la tabla
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'core/partials/tabla_seguimientos.html', context)
    
    return render(request, 'core/seguimientos.html', context)

def api_opciones_gestion(request):
    """Endpoint API que devuelve las opciones disponibles para los campos de gestión."""
    # Permitir acceso sin autenticación para fines de prueba
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'No autorizado'}, status=401)
    
    # Agregar encabezados CORS para permitir solicitudes desde cualquier origen
    response = JsonResponse({}) # Placeholder, se reemplazará más adelante
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    # Para solicitudes OPTIONS, devolver solo los encabezados CORS
    if request.method == "OPTIONS":
        return response
    
    nivel = request.GET.get('nivel', '1')
    padre = request.GET.get('padre', '')
    
    # Definir las opciones para cada nivel
    opciones = {
        '1': [
            {'valor': 'informacion', 'texto': 'Información'},
            {'valor': 'acuerdo', 'texto': 'Acuerdo de Pago'},
            {'valor': 'recordatorio', 'texto': 'Recordatorio'},
            {'valor': 'otro', 'texto': 'Otro'}
        ],
        '2': {
            'informacion': [
                {'valor': 'datos_contacto', 'texto': 'Actualización de Datos'},
                {'valor': 'estado_cuenta', 'texto': 'Estado de Cuenta'},
                {'valor': 'productos', 'texto': 'Información de Productos'}
            ],
            'acuerdo': [
                {'valor': 'pago_total', 'texto': 'Pago Total'},
                {'valor': 'pago_parcial', 'texto': 'Pago Parcial'},
                {'valor': 'refinanciacion', 'texto': 'Refinanciación'}
            ],
            'recordatorio': [
                {'valor': 'vencimiento', 'texto': 'Vencimiento Próximo'},
                {'valor': 'mora', 'texto': 'Cuenta en Mora'},
                {'valor': 'compromiso', 'texto': 'Compromiso Previo'}
            ],
            'otro': [
                {'valor': 'queja', 'texto': 'Queja o Reclamo'},
                {'valor': 'solicitud', 'texto': 'Solicitud Especial'}
            ]
        },
        '3': {
            'datos_contacto': [
                {'valor': 'telefono', 'texto': 'Teléfono'},
                {'valor': 'direccion', 'texto': 'Dirección'},
                {'valor': 'email', 'texto': 'Correo Electrónico'}
            ],
            'estado_cuenta': [
                {'valor': 'saldo', 'texto': 'Saldo Actual'},
                {'valor': 'movimientos', 'texto': 'Últimos Movimientos'}
            ],
            'pago_total': [
                {'valor': 'descuento', 'texto': 'Con Descuento'},
                {'valor': 'sin_descuento', 'texto': 'Sin Descuento'}
            ],
            'pago_parcial': [
                {'valor': 'cuotas', 'texto': 'En Cuotas'},
                {'valor': 'unico', 'texto': 'Pago Único'}
            ],
            # Más opciones para otros valores de nivel 2...
        }
    }
    
    # Determinar qué opciones devolver
    resultado = []
    if nivel == '1':
        resultado = opciones['1']
    elif nivel == '2' and padre in opciones['2']:
        resultado = opciones['2'][padre]
    elif nivel == '3' and padre in opciones['3']:
        resultado = opciones['3'][padre]
    
    # Crear la respuesta con los datos y agregar encabezados CORS
    response = JsonResponse({
        'opciones': resultado,
        'nivel': nivel,
        'padre': padre
    })
    
    # Agregar encabezados CORS
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


def api_seguimientos_proximos(request):
    """Endpoint API que devuelve los seguimientos que están próximos a realizarse."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    # Obtener la fecha y hora actual (asegurando que use la zona horaria de Bogotá)
    ahora = timezone.localtime(timezone.now())
    hora_actual = ahora.time()
    fecha_actual = ahora.date()
    
    # Log para depuración de zona horaria
    print(f"DEBUG: Zona horaria del servidor: {timezone.get_current_timezone()}")
    print(f"DEBUG: Hora UTC: {timezone.now()}")
    print(f"DEBUG: Hora local (Bogotá): {ahora}")
    
    # Crear una ventana de tiempo más amplia (30 minutos) para capturar seguimientos próximos
    limite_tiempo = (ahora + timezone.timedelta(minutes=30)).time()
    
    # Para seguimientos sin hora específica, considerar todo el día
    # También considerar seguimientos del día anterior que no se hayan completado
    ayer = fecha_actual - timezone.timedelta(days=1)
    
    # Log de depuración
    print(f"DEBUG: Buscando seguimientos próximos a las {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DEBUG: Hora actual: {hora_actual}, Límite: {limite_tiempo}")
    
    # Filtrar seguimientos pendientes (de hoy o de ayer) que no estén completados
    seguimientos_pendientes = Gestion.objects.filter(
        seguimiento_requerido=True,
        seguimiento_completado=False,
        fecha_proximo_seguimiento__in=[fecha_actual, ayer]
    )
    
    # Log de depuración para ver cuántos seguimientos pendientes hay en total
    print(f"DEBUG: Total de seguimientos pendientes encontrados: {seguimientos_pendientes.count()}")
    for seg in seguimientos_pendientes:
        print(f"DEBUG: Seguimiento ID {seg.id}, Cliente: {seg.cliente.nombre_completo}, "  
              f"Fecha: {seg.fecha_proximo_seguimiento}, Hora: {seg.hora_proximo_seguimiento or 'No especificada'}, "  
              f"Usuario: {seg.usuario_gestion.username}")
    
    # Filtrar por usuario actual
    seguimientos_usuario = seguimientos_pendientes.filter(usuario_gestion=request.user)
    print(f"DEBUG: Seguimientos asignados al usuario actual: {seguimientos_usuario.count()}")
    
    # Filtrar por hora si está disponible o incluir todos si no tienen hora específica
    seguimientos_a_notificar = []
    for seguimiento in seguimientos_usuario:
        incluir = False
        
        # Si es de hoy
        if seguimiento.fecha_proximo_seguimiento == fecha_actual:
            if seguimiento.hora_proximo_seguimiento:
                # Incluir si la hora está dentro de la ventana de 30 minutos
                if hora_actual <= seguimiento.hora_proximo_seguimiento <= limite_tiempo:
                    incluir = True
                    print(f"DEBUG: Incluyendo seguimiento ID {seguimiento.id} - hora dentro de ventana")
                # MODIFICACIÓN: Incluir también si la hora ya pasó (seguimientos pendientes de hoy)
                elif hora_actual > seguimiento.hora_proximo_seguimiento:
                    incluir = True
                    print(f"DEBUG: Incluyendo seguimiento ID {seguimiento.id} - hora ya pasó hoy")
            else:
                # Si no tiene hora específica, incluirlo durante todo el día
                incluir = True
                print(f"DEBUG: Incluyendo seguimiento ID {seguimiento.id} - sin hora específica")
        
        # Si es de ayer y no se atendió
        elif seguimiento.fecha_proximo_seguimiento == ayer:
            # Incluir seguimientos de ayer que no se atendieron
            incluir = True
            print(f"DEBUG: Incluyendo seguimiento ID {seguimiento.id} - de ayer sin atender")
        
        if incluir:
            seguimientos_a_notificar.append(seguimiento)
    
    # Preparar la respuesta
    seguimientos_data = []
    for seguimiento in seguimientos_a_notificar:
        hora_texto = seguimiento.hora_proximo_seguimiento.strftime('%H:%M') if seguimiento.hora_proximo_seguimiento else 'No especificada'
        fecha_texto = seguimiento.fecha_proximo_seguimiento.strftime('%d/%m/%Y')
        
        # Indicar si es un seguimiento atrasado
        es_atrasado = seguimiento.fecha_proximo_seguimiento < fecha_actual
        estado = "Atrasado" if es_atrasado else "Pendiente"
        
        seguimientos_data.append({
            'id': seguimiento.id,
            'cliente_nombre': seguimiento.cliente.nombre_completo,
            'cliente_documento': seguimiento.cliente.documento,
            'fecha_seguimiento': fecha_texto,
            'hora_seguimiento': hora_texto,
            'observaciones': seguimiento.observaciones_generales or 'Sin observaciones',
            'url': reverse('detalle_cliente', kwargs={'documento_cliente': seguimiento.cliente.documento}),
            'estado': estado
        })
    
    print(f"DEBUG: Total de seguimientos a notificar: {len(seguimientos_data)}")
    
    # Crear la respuesta con los datos y agregar encabezados CORS
    response = JsonResponse({
        'seguimientos': seguimientos_data,
        'total': len(seguimientos_data),
        'timestamp': ahora.isoformat(),
        'debug_info': {
            'fecha_actual': fecha_actual.isoformat(),
            'hora_actual': hora_actual.isoformat(),
            'limite_tiempo': limite_tiempo.isoformat()
        }
    })
    
    # Agregar encabezados CORS
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

@login_required
@user_passes_test(es_admin)
def carga_clientes(request):
    """
    Vista para cargar clientes masivamente desde un archivo Excel o CSV
{{ ... }}
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
    clientes_mismo_documento = Cliente.objects.filter(documento=documento_cliente).order_by('-id')
    if not clientes_mismo_documento.exists():
        raise Http404("Cliente no encontrado con el documento proporcionado.")

    cliente_representativo = clientes_mismo_documento.first()
    # Convertir a lista para evitar múltiples consultas a la base de datos si se itera varias veces
    referencias_cliente_list = list(clientes_mismo_documento)

    # Lógica de consolidación de datos financieros (adaptada de la original)
    deuda_total_consolidada = sum(c.deuda_total for c in referencias_cliente_list if c.deuda_total is not None)
    productos_count = len(referencias_cliente_list)
    
    edades_cartera = [c.total_dias_mora for c in referencias_cliente_list if c.total_dias_mora is not None]
    edad_cartera_promedio = sum(edades_cartera) / len(edades_cartera) if edades_cartera else 0
    
    valor_pagado_total = sum(c.total_pagado for c in referencias_cliente_list if c.total_pagado is not None)
    saldo_capital_total = sum(c.principal for c in referencias_cliente_list if c.principal is not None)
    intereses_corrientes_total = sum(c.intereses for c in referencias_cliente_list if c.intereses is not None)
    intereses_mora_total = sum(0 for c in referencias_cliente_list) # Campo no existente, sumando 0 temporalmente
    gastos_cobranza_total = sum(0 for c in referencias_cliente_list) # Campo no existente, sumando 0 temporalmente
    otros_conceptos_total = sum(c.otros_cargos for c in referencias_cliente_list if c.otros_cargos is not None)

    # Inicializar el formulario de gestión. El campo 'cliente' se pre-rellena con el cliente_representativo.
    # Esto es útil si el campo 'cliente' es visible en el formulario.
    # Si está oculto y se asigna solo en backend, `GestionForm()` sería suficiente para GET.
    gestion_form = GestionForm(initial={'cliente': cliente_representativo})

    if request.method == 'POST':
        # Asumimos que el POST es para guardar una gestión.
        # Para mayor robustez, se podría añadir un 'name' al botón de submit del formulario de gestión
        # y comprobarlo aquí: if 'nombre_del_boton_submit_gestion' in request.POST:
        gestion_form_posted = GestionForm(request.POST)
        if gestion_form_posted.is_valid():
            gestion = gestion_form_posted.save(commit=False)
            # Asociar la gestión al cliente_representativo (el registro más reciente con ese documento)
            gestion.cliente = cliente_representativo 
            gestion.usuario_gestion = request.user
            gestion.save()
            messages.success(request, f'Gestión para {cliente_representativo.nombre_completo} guardada exitosamente.')
            # Redirigir a la misma página para ver la nueva gestión y limpiar el formulario (evita re-POST)
            return redirect('detalle_cliente', documento_cliente=documento_cliente)
        else:
            messages.error(request, 'Error al guardar la gestión. Por favor revise el formulario.')
            gestion_form = gestion_form_posted # Pasa el formulario con errores para mostrar en la plantilla
    
    # Gestiones para la pestaña de historial. Mostrar todas las gestiones asociadas a CUALQUIER cliente con ese documento.
    # Ordenadas por fecha de gestión descendente, y luego por ID descendente como desempate.
    gestiones_del_cliente = Gestion.objects.filter(cliente__documento=documento_cliente).order_by('-fecha_hora_gestion', '-id')[:20]

    # Obtener la fecha actual para comparaciones en la plantilla
    today = datetime.now().date()
    
    context = {
        'cliente_representativo': cliente_representativo,
        'referencias_cliente': referencias_cliente_list, 
        'documento_cliente': documento_cliente,
        'deuda_total_consolidada': deuda_total_consolidada,
        'productos_count': productos_count,
        'edad_cartera_promedio': edad_cartera_promedio,
        'valor_pagado_total': valor_pagado_total,
        'saldo_capital_total': saldo_capital_total,
        'intereses_corrientes_total': intereses_corrientes_total,
        'intereses_mora_total': intereses_mora_total,
        'gastos_cobranza_total': gastos_cobranza_total,
        'otros_conceptos_total': otros_conceptos_total,
        'gestion_form': gestion_form, # Para la pestaña de registrar gestión
        'gestiones_cliente': gestiones_del_cliente, # Para la pestaña de historial de gestiones
        'titulo_pagina': f"Detalle Cliente: {cliente_representativo.nombre_completo}",
        'today': today, # Fecha actual para comparaciones en la plantilla
        # Estos campos existían en la plantilla original, asegurarse que se calculan o se obtienen si son necesarios.
        # 'contactos_adicionales': cliente_representativo.contactos_adicionales.all() if hasattr(cliente_representativo, 'contactos_adicionales') else [],
        # 'direcciones_adicionales': cliente_representativo.direcciones_adicionales.all() if hasattr(cliente_representativo, 'direcciones_adicionales') else [],
    }
    return render(request, 'core/detalle_cliente.html', context)


# La vista agregar_gestion_cliente (líneas 521-544 de la versión anterior) ya no es necesaria
# y será eliminada en un paso posterior.
# def agregar_gestion_cliente(request, documento_cliente):
#    ...

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
    usuarios = User.objects.annotate(
        fullname=Concat('first_name', Value(' '), 'last_name')
    ).order_by('username')
    grupos = Group.objects.all().order_by('name')

    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
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

@login_required
def registrar_nueva_gestion(request):
    buscar_form = BuscarClienteForm()
    gestion_form = GestionForm()
    cliente_encontrado = None
    # total_deuda_agrupada = 0 # Se implementará más adelante

    if request.method == 'POST':
        if 'buscar_cliente' in request.POST:
            buscar_form = BuscarClienteForm(request.POST)
            if buscar_form.is_valid():
                documento = buscar_form.cleaned_data['documento']
                # Usar filter() y order_by() para obtener el más reciente si hay duplicados
                clientes_con_documento = Cliente.objects.filter(documento=documento).order_by('-id')
                
                if clientes_con_documento.exists():
                    cliente_para_sesion = clientes_con_documento.first() # Tomar el primero (más reciente por -id)
                    request.session['cliente_encontrado_id'] = cliente_para_sesion.id
                    messages.success(request, f"Cliente '{cliente_para_sesion.nombre_completo}' (ID: {cliente_para_sesion.id}) encontrado. Mostrando el registro más reciente.")
                else:
                    request.session.pop('cliente_encontrado_id', None)
                    messages.error(request, "Cliente no encontrado con el documento proporcionado.")
                return redirect('registrar_nueva_gestion')

        elif 'guardar_gestion' in request.POST:
            cliente_id_sesion = request.session.get('cliente_encontrado_id')
            if not cliente_id_sesion:
                messages.error(request, "No hay cliente seleccionado. Por favor, busque un cliente primero.")
                return redirect('registrar_nueva_gestion')

            try:
                # Usar el ID de la sesión que ya es único
                cliente_para_gestion = Cliente.objects.get(id=cliente_id_sesion)
            except Cliente.DoesNotExist:
                messages.error(request, "El cliente seleccionado ya no existe. Busque de nuevo.")
                request.session.pop('cliente_encontrado_id', None)
                return redirect('registrar_nueva_gestion')

            gestion_form_data = GestionForm(request.POST)
            if gestion_form_data.is_valid():
                gestion = gestion_form_data.save(commit=False)
                gestion.cliente = cliente_para_gestion
                gestion.usuario_gestion = request.user
                gestion.save()
                messages.success(request, f"Gestión guardada para {cliente_para_gestion.nombre_completo}.")
                request.session.pop('cliente_encontrado_id', None)
                return redirect('registrar_nueva_gestion')
            else:
                # Si el form de gestión no es válido, necesitamos repopular el cliente_encontrado
                # para que la plantilla muestre la sección de registrar gestión.
                cliente_encontrado = cliente_para_gestion 
                gestion_form = gestion_form_data # Pasar el form con errores para mostrar los errores
                messages.error(request, "Error al guardar la gestión. Por favor, revise los campos del formulario.")

    # Lógica para GET o si POST de guardar_gestion falla y necesitamos mostrar el form de nuevo
    if not cliente_encontrado: # Solo si no venimos de un error al guardar gestion (donde ya se seteó)
        cliente_id_sesion = request.session.get('cliente_encontrado_id')
        if cliente_id_sesion:
            try:
                cliente_encontrado = Cliente.objects.get(id=cliente_id_sesion)
                # Pre-llenar el campo cliente en el formulario de gestión
                gestion_form = GestionForm(initial={'cliente': cliente_encontrado})
            except Cliente.DoesNotExist:
                # Limpiar la sesión si el cliente ya no existe
                request.session.pop('cliente_encontrado_id', None)
                cliente_encontrado = None # Asegurarse que no se muestra nada si no existe

    context = {
        'buscar_form': buscar_form,
        'gestion_form': gestion_form,
        'cliente_encontrado': cliente_encontrado,
        'titulo_pagina': "Registrar Nueva Gestión"
    }
    return render(request, 'core/registrar_nueva_gestion.html', context)

@login_required
@user_passes_test(es_admin)
def enviar_email_prueba(request, documento_cliente):
    """
    Vista para enviar un correo electrónico de prueba al cliente.
    """
    # Obtener todos los clientes con ese documento y ordenarlos por ID descendente
    clientes_mismo_documento = Cliente.objects.filter(documento=documento_cliente).order_by('-id')
    
    if not clientes_mismo_documento.exists():
        raise Http404("Cliente no encontrado con el documento proporcionado.")
    
    # Tomar el cliente más reciente (el primero después de ordenar por -id)
    cliente_representativo = clientes_mismo_documento.first()
    
    if not cliente_representativo.email:
        messages.error(request, f'No se puede enviar correo porque el cliente {cliente_representativo.nombre_completo} no tiene una dirección de email registrada.')
        return redirect('detalle_cliente', documento_cliente=documento_cliente)
    
    # Enviar el correo de prueba
    resultado = enviar_correo_prueba(cliente_representativo.email, cliente_representativo.nombre_completo)
    
    if resultado:
        messages.success(request, f'Correo de prueba enviado correctamente a {cliente_representativo.email}.')
    else:
        messages.error(request, f'Error al enviar el correo de prueba a {cliente_representativo.email}. Verifique la configuración SMTP.')
    
    return redirect('detalle_cliente', documento_cliente=documento_cliente)

@login_required
def marcar_seguimiento_completado(request, seguimiento_id):
    """
    Marca un seguimiento como completado y redirige a la página anterior.
    """
    if request.method == 'POST':
        try:
            seguimiento = Gestion.objects.get(id=seguimiento_id, usuario_gestion=request.user)
            seguimiento.seguimiento_completado = True
            seguimiento.save()
            
            # Mensaje de éxito
            messages.success(request, f'Seguimiento para {seguimiento.cliente.nombre_completo} marcado como completado.')
            
            # Limpiar la notificación del localStorage si se está usando la API JavaScript
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Seguimiento ID {seguimiento_id} marcado como completado',
                    'seguimiento_id': seguimiento_id
                })
                
        except Gestion.DoesNotExist:
            messages.error(request, 'No se encontró el seguimiento solicitado o no tienes permiso para modificarlo.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontró el seguimiento solicitado o no tienes permiso para modificarlo.'
                }, status=404)
    
    # Redirigir a la página de referencia o a la lista de seguimientos por defecto
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('seguimientos')


# REPORTES


# Vistas AJAX para los desplegables dependientes
def get_opciones_nivel1(request):
    """
    Vista AJAX que devuelve las opciones para el desplegable de nivel 1 según el estado de contacto seleccionado.
    """
    estado_contacto_id = request.GET.get('estado_contacto_id')
    opciones_nivel1_data = {}
    
    # Importar aquí para evitar dependencias circulares
    from .models import GESTION_OPCIONES
    
    if estado_contacto_id and estado_contacto_id in GESTION_OPCIONES:
        opciones_nivel1_data = GESTION_OPCIONES[estado_contacto_id].get('nivel1', {})
    
    opciones_para_select = [{'value': key, 'label': data['label']} for key, data in opciones_nivel1_data.items()]
    return JsonResponse(opciones_para_select, safe=False)


def get_opciones_nivel2(request):
    """
    Vista AJAX que devuelve las opciones para el desplegable de nivel 2 según el estado de contacto 
    y el tipo de gestión nivel 1 seleccionados.
    """
    estado_contacto_id = request.GET.get('estado_contacto_id')
    tipo_gestion_n1_id = request.GET.get('tipo_gestion_n1_id')
    opciones_nivel2_data = {}
    
    # Importar aquí para evitar dependencias circulares
    from .models import GESTION_OPCIONES
    
    if estado_contacto_id and tipo_gestion_n1_id and \
       estado_contacto_id in GESTION_OPCIONES and \
       GESTION_OPCIONES[estado_contacto_id].get('nivel1') and \
       tipo_gestion_n1_id in GESTION_OPCIONES[estado_contacto_id]['nivel1']:
        opciones_nivel2_data = GESTION_OPCIONES[estado_contacto_id]['nivel1'][tipo_gestion_n1_id].get('nivel2', {})

    opciones_para_select = [{'value': key, 'label': text} for key, text in opciones_nivel2_data.items()]
    return JsonResponse(opciones_para_select, safe=False)