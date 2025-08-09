from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import csv
import pandas as pd
from io import BytesIO

from .models import (
    VentaTarjetaPlata,
    ClienteTarjetaPlata,
    AuditoriaBackofficeTarjetaPlata,
    GestionBackofficeTarjetaPlata,
    ESTADO_VENTA_TARJETA_CHOICES
)
from .forms import (
    VentaTarjetaPlataForm,
    ClienteTarjetaPlataForm,
    GestionBackofficeForm,
    AuditoriaBackofficeForm,
    CargaMasivaClientesForm,
    FiltroVentasForm
)
from core.models import Empleado


@login_required
def dashboard(request):
    """Dashboard principal de Tarjeta Plata"""
    
    # Estadísticas generales
    total_ventas = VentaTarjetaPlata.objects.count()
    ventas_nuevas = VentaTarjetaPlata.objects.filter(estado_venta='nueva').count()
    ventas_aceptadas = VentaTarjetaPlata.objects.filter(estado_venta='aceptada').count()
    ventas_rechazadas = VentaTarjetaPlata.objects.filter(estado_venta='rechazada').count()
    
    # Estadísticas del usuario actual
    if request.user.groups.filter(name='asesor').exists():
        mis_ventas = VentaTarjetaPlata.objects.filter(agente=request.user).count()
        mis_ventas_hoy = VentaTarjetaPlata.objects.filter(
            agente=request.user,
            fecha_creacion__date=timezone.now().date()
        ).count()
    else:
        mis_ventas = 0
        mis_ventas_hoy = 0
    
    # Ventas por día (últimos 30 días)
    fecha_inicio = timezone.now().date() - timedelta(days=30)
    ventas_por_dia = VentaTarjetaPlata.objects.filter(
        fecha_creacion__date__gte=fecha_inicio
    ).extra(
        select={'fecha': 'DATE(fecha_creacion)'}
    ).values('fecha').annotate(
        total=Count('id')
    ).order_by('fecha')
    
    # Preparar datos para gráficos
    fechas = []
    totales = []
    for venta in ventas_por_dia:
        fechas.append(venta['fecha'].strftime('%Y-%m-%d'))
        totales.append(venta['total'])
    
    # Ventas por asesor del mes actual - datos para gráfica de barras horizontales
    from django.contrib.auth.models import User
    # Obtener el primer y último día del mes actual
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    if hoy.month == 12:
        ultimo_dia_mes = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        ultimo_dia_mes = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
    
    ventas_por_asesor = VentaTarjetaPlata.objects.filter(
        fecha_creacion__date__gte=primer_dia_mes,
        fecha_creacion__date__lte=ultimo_dia_mes
    ).values(
        'agente__first_name', 'agente__last_name', 'agente__username'
    ).annotate(
        total_ventas=Count('id')
    ).order_by('-total_ventas')[:10]  # Top 10 asesores del mes actual
    
    # Preparar datos para la gráfica de asesores
    asesores_nombres = []
    asesores_ventas = []
    for asesor in ventas_por_asesor:
        # Crear nombre completo del asesor
        if asesor['agente__first_name'] and asesor['agente__last_name']:
            nombre_completo = f"{asesor['agente__first_name']} {asesor['agente__last_name']}"
        else:
            nombre_completo = asesor['agente__username'] or 'Usuario sin nombre'
        
        asesores_nombres.append(nombre_completo)
        asesores_ventas.append(asesor['total_ventas'])
    
    context = {
        'total_ventas': total_ventas,
        'ventas_nuevas': ventas_nuevas,
        'ventas_aceptadas': ventas_aceptadas,
        'ventas_rechazadas': ventas_rechazadas,
        'mis_ventas': mis_ventas,
        'mis_ventas_hoy': mis_ventas_hoy,
        'fechas_json': json.dumps(fechas),
        'totales_json': json.dumps(totales),
        'asesores_nombres_json': json.dumps(asesores_nombres),
        'asesores_ventas_json': json.dumps(asesores_ventas),
        'es_asesor': request.user.groups.filter(name='asesor').exists(),
        'es_backoffice': request.user.groups.filter(name='backoffice').exists(),
    }
    
    return render(request, 'tarjeta_plata/dashboard.html', context)


@login_required
def lista_ventas(request):
    """Lista de ventas con filtros"""
    
    ventas = VentaTarjetaPlata.objects.all().select_related('agente', 'backoffice')
    
    # Si es asesor, solo mostrar sus ventas
    if request.user.groups.filter(name='asesor').exists():
        ventas = ventas.filter(agente=request.user)
    
    # Aplicar filtros
    form = FiltroVentasForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['fecha_inicio']:
            ventas = ventas.filter(fecha_creacion__date__gte=form.cleaned_data['fecha_inicio'])
        if form.cleaned_data['fecha_fin']:
            ventas = ventas.filter(fecha_creacion__date__lte=form.cleaned_data['fecha_fin'])
        if form.cleaned_data['estado']:
            ventas = ventas.filter(estado_venta=form.cleaned_data['estado'])
        if form.cleaned_data['agente']:
            ventas = ventas.filter(agente=form.cleaned_data['agente'])
        if form.cleaned_data['buscar']:
            buscar = form.cleaned_data['buscar']
            ventas = ventas.filter(
                Q(nombre__icontains=buscar) |
                Q(rfc__icontains=buscar) |
                Q(telefono__icontains=buscar) |
                Q(id_preap__icontains=buscar)
            )
    
    # Paginación
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_ventas': ventas.count(),
    }
    
    return render(request, 'tarjeta_plata/lista_ventas.html', context)


@login_required
def crear_venta(request):
    """Crear nueva venta de tarjeta de crédito"""
    
    # DEBUG: Log del usuario actual
    print(f"[DEBUG] Usuario actual: {request.user} (ID: {request.user.id})")
    print(f"[DEBUG] Grupos del usuario: {[g.name for g in request.user.groups.all()]}")
    
    if request.method == 'POST':
        # DEBUG: Log cuando se recibe POST
        print(f"[DEBUG] Método POST recibido en crear_venta")
        print(f"[DEBUG] Datos POST recibidos: {dict(request.POST)}")
        
        form = VentaTarjetaPlataForm(request.POST)
        
        # DEBUG: Log de validación del formulario
        print(f"[DEBUG] Validando formulario...")
        is_valid = form.is_valid()
        print(f"[DEBUG] Formulario válido: {is_valid}")
        
        if is_valid:
            print(f"[DEBUG] Formulario es válido, procediendo a guardar...")
            print(f"[DEBUG] Datos limpios del formulario: {form.cleaned_data}")
            
            try:
                print(f"[DEBUG] Creando instancia de venta...")
                venta = form.save(commit=False)
                print(f"[DEBUG] Venta creada (sin guardar): {venta}")
                
                print(f"[DEBUG] Asignando agente: {request.user}")
                venta.agente = request.user
                
                print(f"[DEBUG] Guardando venta en base de datos...")
                venta.save()
                print(f"[DEBUG] Venta guardada exitosamente con ID: {venta.id}")
                print(f"[DEBUG] ID PREAP de la venta: {venta.id_preap}")
                
                messages.success(request, f'Venta {venta.id_preap} creada exitosamente.')
                print(f"[DEBUG] Redirigiendo a detalle_venta con ID: {venta.id}")
                return redirect('tarjeta_plata:detalle_venta', venta_id=venta.id)
                
            except Exception as e:
                print(f"[ERROR] Excepción al guardar la venta: {str(e)}")
                print(f"[ERROR] Tipo de excepción: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback completo: {traceback.format_exc()}")
                messages.error(request, f'Error al guardar la venta: {str(e)}')
        else:
            # DEBUG: Log de errores del formulario
            print(f"[DEBUG] Formulario NO es válido")
            print(f"[DEBUG] Errores del formulario: {form.errors}")
            print(f"[DEBUG] Errores no de campo: {form.non_field_errors()}")
            
            # Agregar mensaje de error cuando el formulario no es válido
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        # DEBUG: Log cuando es GET
        print(f"[DEBUG] Método GET recibido en crear_venta")
        form = VentaTarjetaPlataForm()
    
    context = {
        'form': form,
        'titulo': 'Nueva Venta de Tarjeta de Crédito',
    }
    
    print(f"[DEBUG] Renderizando template con contexto")
    return render(request, 'tarjeta_plata/crear_venta.html', context)


@login_required
def detalle_venta(request, venta_id):
    """Detalle de una venta específica"""
    
    venta = get_object_or_404(VentaTarjetaPlata, id=venta_id)
    
    # Verificar permisos
    if request.user.groups.filter(name='asesor').exists() and venta.agente != request.user:
        messages.error(request, 'No tienes permisos para ver esta venta.')
        return redirect('tarjeta_plata:lista_ventas')
    
    # Obtener gestiones del backoffice
    gestiones = venta.gestiones_backoffice.all().select_related('backoffice')
    
    # Obtener auditorías
    auditorias = venta.auditorias_backoffice.all().select_related('auditor')
    
    context = {
        'venta': venta,
        'gestiones': gestiones,
        'auditorias': auditorias,
        'puede_editar': request.user == venta.agente or request.user.groups.filter(name__in=['administrador', 'backoffice']).exists(),
    }
    
    return render(request, 'tarjeta_plata/detalle_venta.html', context)


@login_required
def editar_venta(request, venta_id):
    """Editar una venta existente"""
    
    venta = get_object_or_404(VentaTarjetaPlata, id=venta_id)
    
    # Verificar permisos
    if not (request.user == venta.agente or request.user.groups.filter(name__in=['administrador', 'backoffice']).exists()):
        messages.error(request, 'No tienes permisos para editar esta venta.')
        return redirect('tarjeta_plata:detalle_venta', venta_id=venta.id)
    
    if request.method == 'POST':
        form = VentaTarjetaPlataForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada exitosamente.')
            return redirect('tarjeta_plata:detalle_venta', venta_id=venta.id)
    else:
        form = VentaTarjetaPlataForm(instance=venta)
    
    context = {
        'form': form,
        'venta': venta,
        'titulo': f'Editar Venta {venta.id_preap}',
    }
    
    return render(request, 'tarjeta_plata/editar_venta.html', context)


@login_required
def bandeja_nuevas(request):
    """Bandeja de ventas nuevas para validación del backoffice"""
    
    # Solo backoffice y administradores pueden acceder
    if not request.user.groups.filter(name__in=['backoffice', 'administrador']).exists():
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('tarjeta_plata:dashboard')
    
    ventas = VentaTarjetaPlata.objects.filter(estado_venta='nueva').select_related('agente')
    
    # Paginación
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'titulo': 'Ventas Nuevas - Pendientes de Validación',
        'total_ventas': ventas.count(),
    }
    
    return render(request, 'tarjeta_plata/bandeja_nuevas.html', context)


@login_required
def bandeja_aceptadas(request):
    """Bandeja de ventas aceptadas"""
    
    ventas = VentaTarjetaPlata.objects.filter(estado_venta='aceptada').select_related('agente', 'backoffice')
    
    # Si es asesor, solo mostrar sus ventas
    if request.user.groups.filter(name='asesor').exists():
        ventas = ventas.filter(agente=request.user)
    
    # Paginación
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'titulo': 'Ventas Aceptadas',
        'total_ventas': ventas.count(),
    }
    
    return render(request, 'tarjeta_plata/bandeja_aceptadas.html', context)


@login_required
def bandeja_rechazadas(request):
    """Bandeja de ventas rechazadas"""
    
    ventas = VentaTarjetaPlata.objects.filter(estado_venta='rechazada').select_related('agente', 'backoffice')
    
    # Si es asesor, solo mostrar sus ventas
    if request.user.groups.filter(name='asesor').exists():
        ventas = ventas.filter(agente=request.user)
    
    # Paginación
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'titulo': 'Ventas Rechazadas',
        'total_ventas': ventas.count(),
    }
    
    return render(request, 'tarjeta_plata/bandeja_rechazadas.html', context)


@login_required
def validar_venta(request, venta_id):
    """Validar una venta (cambiar estado)"""
    
    # Solo backoffice y administradores pueden validar
    if not request.user.groups.filter(name__in=['backoffice', 'administrador']).exists():
        messages.error(request, 'No tienes permisos para validar ventas.')
        return redirect('tarjeta_plata:dashboard')
    
    venta = get_object_or_404(VentaTarjetaPlata, id=venta_id)
    
    if request.method == 'POST':
        form = GestionBackofficeForm(request.POST, request.FILES)
        if form.is_valid():
            # Crear la gestión
            gestion = form.save(commit=False)
            gestion.venta = venta
            gestion.backoffice = request.user
            gestion.estado_anterior = venta.estado_venta
            gestion.estado_nuevo = form.cleaned_data['nuevo_estado']
            gestion.save()
            
            # Actualizar el estado de la venta
            venta.estado_venta = form.cleaned_data['nuevo_estado']
            venta.backoffice = request.user
            venta.save()
            
            messages.success(request, f'Venta {venta.id_preap} validada como {venta.get_estado_venta_display()}.')
            return redirect('tarjeta_plata:bandeja_nuevas')
    else:
        form = GestionBackofficeForm()
    
    context = {
        'form': form,
        'venta': venta,
        'titulo': f'Validar Venta {venta.id_preap}',
    }
    
    return render(request, 'tarjeta_plata/validar_venta.html', context)


@login_required
def crear_auditoria(request, venta_id):
    """Crear auditoría para una venta"""
    
    # Solo backoffice y administradores pueden crear auditorías
    if not request.user.groups.filter(name__in=['backoffice', 'administrador']).exists():
        messages.error(request, 'No tienes permisos para crear auditorías.')
        return redirect('tarjeta_plata:dashboard')
    
    venta = get_object_or_404(VentaTarjetaPlata, id=venta_id)
    
    if request.method == 'POST':
        form = AuditoriaBackofficeForm(request.POST, request.FILES)
        if form.is_valid():
            auditoria = form.save(commit=False)
            auditoria.venta = venta
            auditoria.auditor = request.user
            auditoria.save()
            
            messages.success(request, f'Auditoría creada para la venta {venta.id_preap}.')
            return redirect('tarjeta_plata:detalle_venta', venta_id=venta.id)
    else:
        form = AuditoriaBackofficeForm()
    
    context = {
        'form': form,
        'venta': venta,
        'titulo': f'Crear Auditoría - Venta {venta.id_preap}',
    }
    
    return render(request, 'tarjeta_plata/crear_auditoria.html', context)


# Vistas para clientes
@login_required
def lista_clientes(request):
    """Lista de clientes"""
    
    clientes = ClienteTarjetaPlata.objects.all()
    
    # Búsqueda
    buscar = request.GET.get('buscar')
    if buscar:
        clientes = clientes.filter(
            Q(nombre_completo__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(rfc__icontains=buscar) |
            Q(item__icontains=buscar)
        )
    
    # Paginación
    paginator = Paginator(clientes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'buscar': buscar,
        'total_clientes': clientes.count(),
    }
    
    return render(request, 'tarjeta_plata/lista_clientes.html', context)


@login_required
def crear_cliente(request):
    """Crear nuevo cliente"""
    
    if request.method == 'POST':
        form = ClienteTarjetaPlataForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nombre_completo} creado exitosamente.')
            return redirect('tarjeta_plata:detalle_cliente', cliente_id=cliente.id)
    else:
        form = ClienteTarjetaPlataForm()
    
    context = {
        'form': form,
        'titulo': 'Nuevo Cliente',
    }
    
    return render(request, 'tarjeta_plata/crear_cliente.html', context)


@login_required
def detalle_cliente(request, cliente_id):
    """Detalle de un cliente específico"""
    
    cliente = get_object_or_404(ClienteTarjetaPlata, id=cliente_id)
    
    context = {
        'cliente': cliente,
    }
    
    return render(request, 'tarjeta_plata/detalle_cliente.html', context)


@login_required
def editar_cliente(request, cliente_id):
    """Editar un cliente existente"""
    
    cliente = get_object_or_404(ClienteTarjetaPlata, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteTarjetaPlataForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('tarjeta_plata:detalle_cliente', cliente_id=cliente.id)
    else:
        form = ClienteTarjetaPlataForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente {cliente.nombre_completo}',
    }
    
    return render(request, 'tarjeta_plata/editar_cliente.html', context)


@login_required
def carga_masiva_clientes(request):
    """Carga masiva de clientes desde archivo"""
    
    if request.method == 'POST':
        form = CargaMasivaClientesForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            
            try:
                # Procesar archivo según su extensión
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                else:
                    df = pd.read_excel(archivo)
                
                # Validar columnas requeridas
                columnas_requeridas = ['item', 'telefono', 'nombre_completo', 'factibilidad', 'tipo', 'rfc', 'fecha_nacimiento', 'genero', 'email']
                if not all(col in df.columns for col in columnas_requeridas):
                    messages.error(request, f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')
                    return render(request, 'tarjeta_plata/carga_masiva_clientes.html', {'form': form})
                
                # Procesar cada fila
                clientes_creados = 0
                errores = []
                
                for index, row in df.iterrows():
                    try:
                        cliente, created = ClienteTarjetaPlata.objects.get_or_create(
                            item=row['item'],
                            defaults={
                                'telefono': row['telefono'],
                                'nombre_completo': row['nombre_completo'],
                                'factibilidad': row['factibilidad'],
                                'tipo': row['tipo'],
                                'rfc': row['rfc'],
                                'fecha_nacimiento': pd.to_datetime(row['fecha_nacimiento']).date(),
                                'genero': row['genero'],
                                'email': row['email'],
                            }
                        )
                        if created:
                            clientes_creados += 1
                    except Exception as e:
                        errores.append(f'Fila {index + 2}: {str(e)}')
                
                if clientes_creados > 0:
                    messages.success(request, f'Se crearon {clientes_creados} clientes exitosamente.')
                
                if errores:
                    messages.warning(request, f'Se encontraron {len(errores)} errores. Revise el formato del archivo.')
                
                return redirect('tarjeta_plata:lista_clientes')
                
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
    else:
        form = CargaMasivaClientesForm()
    
    context = {
        'form': form,
        'titulo': 'Carga Masiva de Clientes',
    }
    
    return render(request, 'tarjeta_plata/carga_masiva_clientes.html', context)


# Diccionario con los campos disponibles para cada tipo de reporte de tarjeta plata
CAMPOS_DISPONIBLES = {
    'ventas': [
        ('id_preap', 'ID PreAp'),
        ('item', 'Item'),
        ('nombre', 'Nombre'),
        ('ine', 'INE'),
        ('rfc', 'RFC'),
        ('telefono', 'Teléfono'),
        ('correo', 'Correo'),
        ('direccion', 'Dirección'),
        ('codigo_postal', 'Código Postal'),
        ('estado_venta', 'Estado Venta'),
        ('agente__username', 'Agente'),
        ('agente__first_name', 'Nombre Agente'),
        ('agente__last_name', 'Apellido Agente'),
        ('backoffice__username', 'Backoffice'),
        ('backoffice__first_name', 'Nombre Backoffice'),
        ('backoffice__last_name', 'Apellido Backoffice'),
        ('fecha_creacion', 'Fecha Creación'),
        ('fecha_revision', 'Fecha Revisión'),
        ('observaciones', 'Observaciones'),
    ],
    'clientes': [
        ('nombre_completo', 'Nombre Completo'),
        ('telefono', 'Teléfono'),
        ('rfc', 'RFC'),
        ('correo', 'Correo'),
        ('direccion', 'Dirección'),
        ('codigo_postal', 'Código Postal'),
        ('fecha_nacimiento', 'Fecha Nacimiento'),
        ('observaciones', 'Observaciones'),
        ('fecha_creacion', 'Fecha Registro'),
    ],
    'gestiones': [
        ('venta__id_preap', 'ID PreAp Venta'),
        ('venta__item', 'Item Venta'),
        ('venta__nombre', 'Nombre Cliente'),
        ('venta__telefono', 'Teléfono Cliente'),
        ('estado_anterior', 'Estado Anterior'),
        ('nuevo_estado', 'Estado Nuevo'),
        ('observaciones', 'Observaciones'),
        ('backoffice__username', 'Usuario Backoffice'),
        ('backoffice__first_name', 'Nombre Backoffice'),
        ('backoffice__last_name', 'Apellido Backoffice'),
        ('fecha_gestion', 'Fecha Gestión'),
        ('archivo_llamada', 'Archivo Llamada'),
    ],
    'auditorias': [
        ('venta__id_preap', 'ID PreAp Venta'),
        ('venta__item', 'Item Venta'),
        ('venta__nombre', 'Nombre Cliente'),
        ('venta__telefono', 'Teléfono Cliente'),
        ('venta__estado_venta', 'Estado Venta'),
        ('auditor__username', 'Usuario Auditor'),
        ('auditor__first_name', 'Nombre Auditor'),
        ('auditor__last_name', 'Apellido Auditor'),
        ('observaciones', 'Observaciones'),
        ('fecha_auditoria', 'Fecha Auditoría'),
    ],
}

# Vistas de reportes
@login_required
def reportes(request):
    """Vista principal para generar reportes de tarjeta plata"""
    # Determinar si es una solicitud POST o GET
    if request.method == 'POST':
        # Obtener parámetros de filtro de POST
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        tipo_reporte = request.POST.get('tipo_reporte', 'ventas')
        accion = request.POST.get('accion', '')
        campos_seleccionados = request.POST.getlist('campos')
    else:
        # Obtener parámetros de filtro de GET
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo_reporte = request.GET.get('tipo_reporte', 'ventas')
        accion = ''
        campos_seleccionados = request.GET.getlist('campos')
    
    # Establecer fechas por defecto si no se proporcionan
    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
    
    # Si no hay campos seleccionados, seleccionar todos por defecto
    campos_disponibles_tipo = CAMPOS_DISPONIBLES.get(tipo_reporte, [])
    if not campos_seleccionados and campos_disponibles_tipo:
        # Seleccionar todos los campos disponibles por defecto
        campos_seleccionados = [campo[0] for campo in campos_disponibles_tipo]
    
    # Preparar el contexto
    context = {
        'tipos_reporte': [
            ('ventas', 'Ventas'),
            ('clientes', 'Clientes'),
            ('gestiones', 'Gestiones Backoffice'),
            ('auditorias', 'Auditorías'),
        ],
        'tipo_reporte': tipo_reporte,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'campos_disponibles': campos_disponibles_tipo,
        'campos_seleccionados': campos_seleccionados,
        'datos': None,
        'total_registros': 0,
        'mostrando_vista_previa': False,
    }
    
    # Si es una solicitud POST con acción 'aplicar', obtener los datos
    if request.method == 'POST' and accion == 'aplicar':
        try:
            # Convertir fechas
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            
            # Obtener datos según el tipo de reporte
            if tipo_reporte == 'ventas':
                queryset = VentaTarjetaPlata.objects.filter(
                    fecha_creacion__date__gte=fecha_inicio_dt,
                    fecha_creacion__date__lte=fecha_fin_dt
                ).select_related('agente', 'backoffice')
                
                # Si es asesor, solo mostrar sus ventas
                if request.user.groups.filter(name='asesor').exists():
                    queryset = queryset.filter(agente=request.user)
                    
            elif tipo_reporte == 'clientes':
                queryset = ClienteTarjetaPlata.objects.filter(
                    fecha_creacion__date__gte=fecha_inicio_dt,
                    fecha_creacion__date__lte=fecha_fin_dt
                )
                
            elif tipo_reporte == 'gestiones':
                queryset = GestionBackofficeTarjetaPlata.objects.filter(
                    fecha_gestion__date__gte=fecha_inicio_dt,
                    fecha_gestion__date__lte=fecha_fin_dt
                ).select_related('venta', 'backoffice')
                
            elif tipo_reporte == 'auditorias':
                queryset = AuditoriaBackofficeTarjetaPlata.objects.filter(
                    fecha_auditoria__date__gte=fecha_inicio_dt,
                    fecha_auditoria__date__lte=fecha_fin_dt
                ).select_related('venta', 'auditor')
            
            else:
                queryset = VentaTarjetaPlata.objects.none()
            
            # Contar total de registros
            total_registros = queryset.count()
            
            # Limitar a 100 registros para vista previa
            datos = queryset[:100]
            mostrando_vista_previa = total_registros > 100
            
            context.update({
                'datos': datos,
                'total_registros': total_registros,
                'mostrando_vista_previa': mostrando_vista_previa,
            })
            
        except ValueError as e:
            messages.error(request, f'Error en las fechas: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
    
    return render(request, 'tarjeta_plata/reportes.html', context)


@login_required
def reportes_exportar(request):
    """Exportar reportes a Excel con campos seleccionados"""
    
    # Obtener parámetros del formulario
    fecha_inicio = request.POST.get('fecha_inicio')
    fecha_fin = request.POST.get('fecha_fin')
    tipo_reporte = request.POST.get('tipo_reporte', 'ventas')
    campos_seleccionados = request.POST.getlist('campos')
    
    # Establecer fechas por defecto si no se proporcionan
    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
    
    try:
        # Convertir fechas
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Obtener datos según el tipo de reporte
        if tipo_reporte == 'ventas':
            queryset = VentaTarjetaPlata.objects.filter(
                fecha_creacion__date__gte=fecha_inicio_dt,
                fecha_creacion__date__lte=fecha_fin_dt
            ).select_related('agente', 'backoffice')
            
            # Si es asesor, solo exportar sus ventas
            if request.user.groups.filter(name='asesor').exists():
                queryset = queryset.filter(agente=request.user)
                
        elif tipo_reporte == 'clientes':
            queryset = ClienteTarjetaPlata.objects.filter(
                fecha_creacion__date__gte=fecha_inicio_dt,
                fecha_creacion__date__lte=fecha_fin_dt
            )
            
        elif tipo_reporte == 'gestiones':
            queryset = GestionBackofficeTarjetaPlata.objects.filter(
                fecha_gestion__date__gte=fecha_inicio_dt,
                fecha_gestion__date__lte=fecha_fin_dt
            ).select_related('venta', 'backoffice')
            
        elif tipo_reporte == 'auditorias':
            queryset = AuditoriaBackofficeTarjetaPlata.objects.filter(
                fecha_auditoria__date__gte=fecha_inicio_dt,
                fecha_auditoria__date__lte=fecha_fin_dt
            ).select_related('venta', 'auditor')
        
        else:
            queryset = VentaTarjetaPlata.objects.none()
        
        # Si no hay campos seleccionados, usar todos los disponibles
        if not campos_seleccionados:
            campos_disponibles_tipo = CAMPOS_DISPONIBLES.get(tipo_reporte, [])
            campos_seleccionados = [campo[0] for campo in campos_disponibles_tipo]
        
        # Crear DataFrame con los campos seleccionados
        data = []
        campos_dict = dict(CAMPOS_DISPONIBLES.get(tipo_reporte, []))
        
        for obj in queryset:
            row = {}
            for campo in campos_seleccionados:
                etiqueta = campos_dict.get(campo, campo)
                
                # Obtener valor del campo usando getattr anidado
                try:
                    if '__' in campo:
                        # Campo relacionado (ej: agente__username)
                        parts = campo.split('__')
                        valor = obj
                        for part in parts:
                            if valor is None:
                                break
                            valor = getattr(valor, part, None)
                    else:
                        # Campo directo
                        valor = getattr(obj, campo, None)
                    
                    # Formatear valores especiales
                    if valor is None:
                        valor = ''
                    elif hasattr(valor, 'strftime'):
                        # Fechas
                        valor = valor.strftime('%Y-%m-%d %H:%M:%S')
                    elif campo == 'estado_venta' and hasattr(obj, 'get_estado_venta_display'):
                        # Estados con display
                        valor = obj.get_estado_venta_display()
                    elif campo == 'archivo_llamada' and valor:
                        # Archivos - mostrar solo el nombre
                        valor = valor.name if hasattr(valor, 'name') else str(valor)
                    
                    row[etiqueta] = valor
                    
                except Exception as e:
                    row[etiqueta] = f'Error: {str(e)}'
            
            data.append(row)
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Crear respuesta HTTP con Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'reporte_{tipo_reporte}_tarjeta_plata_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=tipo_reporte.title(), index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets[tipo_reporte.title()]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('tarjeta_plata:reportes')


@login_required
def exportar_ventas(request):
    """Exportar ventas a Excel (función legacy mantenida por compatibilidad)"""
    
    ventas = VentaTarjetaPlata.objects.all().select_related('agente', 'backoffice')
    
    # Si es asesor, solo exportar sus ventas
    if request.user.groups.filter(name='asesor').exists():
        ventas = ventas.filter(agente=request.user)
    
    # Crear DataFrame
    data = []
    for venta in ventas:
        data.append({
            'ID PreAp': venta.id_preap,
            'Item': venta.item,
            'Nombre': venta.nombre,
            'INE': venta.ine,
            'RFC': venta.rfc,
            'Teléfono': venta.telefono,
            'Correo': venta.correo,
            'Dirección': venta.direccion,
            'Código Postal': venta.codigo_postal,
            'Estado': venta.get_estado_venta_display(),
            'Agente': venta.agente.get_full_name() if venta.agente else '',
            'Backoffice': venta.backoffice.get_full_name() if venta.backoffice else '',
            'Fecha Creación': venta.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'Fecha Revisión': venta.fecha_revision.strftime('%Y-%m-%d %H:%M:%S') if venta.fecha_revision else '',
            'Observaciones': venta.observaciones or '',
        })
    
    df = pd.DataFrame(data)
    
    # Crear respuesta HTTP con Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="ventas_tarjeta_plata_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Ventas', index=False)
    
    return response


@login_required
def exportar_clientes(request):
    """Exportar clientes a Excel"""
    
    clientes = ClienteTarjetaPlata.objects.all()
    
    # Crear DataFrame
    data = []
    for cliente in clientes:
        data.append({
            'Item': cliente.item,
            'Teléfono': cliente.telefono,
            'Nombre Completo': cliente.nombre_completo,
            'Factibilidad': cliente.get_factibilidad_display(),
            'Tipo': cliente.get_tipo_display(),
            'RFC': cliente.rfc,
            'Fecha Nacimiento': cliente.fecha_nacimiento.strftime('%Y-%m-%d'),
            'Género': cliente.get_genero_display(),
            'Email': cliente.email,
            'Fecha Creación': cliente.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    df = pd.DataFrame(data)
    
    # Crear respuesta HTTP con Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="clientes_tarjeta_plata_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clientes', index=False)
    
    return response


# API endpoints para AJAX


@login_required
def plantilla_clientes(request):
    """Descargar plantilla CSV para carga masiva de clientes"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_clientes_tarjeta_plata.csv"'
    
    writer = csv.writer(response)
    
    # Escribir encabezados
    writer.writerow([
        'nombre',
        'telefono', 
        'correo',
        'direccion',
        'codigo_postal',
        'fecha_nacimiento',
        'observaciones'
    ])
    
    # Escribir filas de ejemplo
    writer.writerow([
        'Juan Pérez García',
        '5551234567',
        'juan.perez@email.com',
        'Av. Reforma 123, Col. Centro',
        '06000',
        '1990-01-15',
        'Cliente potencial para tarjeta de crédito'
    ])
    
    writer.writerow([
        'María González López',
        '5559876543',
        'maria.gonzalez@email.com',
        'Calle Insurgentes 456, Col. Roma',
        '06700',
        '1985-05-20',
        'Interesada en productos bancarios'
    ])
    
    return response


@login_required
def rechazar_venta(request, venta_id):
    """Rechazar una venta específica"""
    
    # Solo backoffice y administradores pueden rechazar ventas
    if not request.user.groups.filter(name__in=['backoffice', 'administrador']).exists():
        messages.error(request, 'No tienes permisos para rechazar ventas.')
        return redirect('tarjeta_plata:dashboard')

    venta = get_object_or_404(VentaTarjetaPlata, id=venta_id)
    
    if request.method == 'POST':
        form = GestionBackofficeForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Crear la gestión de backoffice
            gestion = form.save(commit=False)
            gestion.venta = venta
            gestion.backoffice = request.user
            gestion.estado_anterior = venta.estado_venta
            gestion.estado_nuevo = 'rechazada'
            gestion.save()
            
            # Actualizar el estado de la venta
            venta.estado_venta = 'rechazada'
            venta.backoffice = request.user
            venta.save()
            
            messages.success(request, f'Venta {venta.id_preap} rechazada exitosamente.')
            return redirect('tarjeta_plata:bandeja_nuevas')
        else:
            messages.error(request, 'Error en el formulario. Verifique los datos ingresados.')
            return render(request, 'tarjeta_plata/validar_venta.html', {
                'venta': venta,
                'form': form,
                'titulo': 'Rechazar Venta'
            })
    else:
        form = GestionBackofficeForm()
        # Pre-seleccionar 'rechazada' en el formulario
        form.fields['nuevo_estado'].initial = 'rechazada'
    
    return render(request, 'tarjeta_plata/validar_venta.html', {
        'venta': venta,
        'form': form,
        'titulo': 'Rechazar Venta'
    })


@login_required
def api_ventas_por_dia(request):
    """API para obtener ventas por día para gráficos"""
    
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now().date() - timedelta(days=dias)
    
    ventas_por_dia = VentaTarjetaPlata.objects.filter(
        fecha_creacion__date__gte=fecha_inicio
    ).extra(
        select={'fecha': 'DATE(fecha_creacion)'}
    ).values('fecha').annotate(
        total=Count('id'),
        nuevas=Count('id', filter=Q(estado_venta='nueva')),
        aceptadas=Count('id', filter=Q(estado_venta='aceptada')),
        rechazadas=Count('id', filter=Q(estado_venta='rechazada'))
    ).order_by('fecha')
    
    data = {
        'fechas': [venta['fecha'].strftime('%Y-%m-%d') for venta in ventas_por_dia],
        'totales': [venta['total'] for venta in ventas_por_dia],
        'nuevas': [venta['nuevas'] for venta in ventas_por_dia],
        'aceptadas': [venta['aceptadas'] for venta in ventas_por_dia],
        'rechazadas': [venta['rechazadas'] for venta in ventas_por_dia],
    }
    
    return JsonResponse(data)
