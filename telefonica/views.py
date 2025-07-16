from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import VentaPortabilidad, VentaPrePos, VentaUpgrade, GestionAsesor, GestionBackoffice, Planes_portabilidad, Agendamiento, Comision
from .forms import (
    VentaPortabilidadForm, VentaPrePosForm, VentaUpgradeForm, 
    GestionAsesorForm, GestionBackofficeForm, PlanesPortabilidadForm,
    CorreccionVentaForm
)

# Funciones auxiliares para verificar permisos
def es_asesor(user):
    return user.groups.filter(name='asesor').exists() or user.is_superuser

# Vistas principales
@login_required
def dashboard(request):
    """Vista de dashboard adaptada según el rol del usuario."""
    user = request.user
    es_asesor = user.groups.filter(name='asesor').exists()
    es_backoffice = user.groups.filter(name='backoffice').exists()

    context = {
        'es_asesor': es_asesor,
        'es_backoffice': es_backoffice,
        'ventas_recientes': VentaPortabilidad.objects.none() # Default empty queryset
    }

    # --- Lógica para Asesores ---
    if es_asesor:
        context.update({
            'mis_ventas': VentaPortabilidad.objects.filter(agente=user).count(),
            'mis_ventas_pendientes': VentaPortabilidad.objects.filter(agente=user, estado_venta='pendiente_revision').count(),
            'mis_ventas_devueltas': VentaPortabilidad.objects.filter(agente=user, estado_venta='devuelta').count(),
            'mis_comisiones_pendientes': 0,  # Temporalmente establecido a 0 hasta que se implemente Comision
            'titulo': 'Dashboard Asesor'
        })
        # La tabla principal para un asesor debe mostrar sus propias ventas recientes
        context['ventas_recientes'] = VentaPortabilidad.objects.filter(agente=user).order_by('-fecha_creacion')[:10]

    # --- Lógica para Backoffice ---
    # Esto anulará algunas variables de contexto si el usuario también es asesor, lo cual es correcto.
    if es_backoffice:
        context.update({
            'ventas_pendientes': VentaPortabilidad.objects.filter(estado_venta='pendiente_revision').count(),
            'ventas_devueltas': VentaPortabilidad.objects.filter(estado_venta='devuelta').count(),
            'ventas_aprobadas': VentaPortabilidad.objects.filter(estado_venta='aprobada').count(),
            'ventas_digitadas': VentaPortabilidad.objects.filter(estado_venta='digitada').count(),
            'titulo': 'Dashboard Backoffice'
        })
        # La tabla principal de backoffice debe mostrar todas las ventas recientes pendientes de revisión
        context['ventas_recientes'] = VentaPortabilidad.objects.select_related('plan_adquiere').filter(estado_venta='pendiente_revision').order_by('-fecha_creacion')[:10]

    # --- Lógica para Superusuario (si no está en grupos o es ambos) ---
    if user.is_superuser:
        if es_backoffice and es_asesor:
            context['titulo'] = 'Dashboard General'
        elif not es_backoffice and not es_asesor:
            # Asignar vista de backoffice por defecto a superusuarios sin grupo
            context.update({
                'ventas_pendientes': VentaPortabilidad.objects.filter(estado_venta='pendiente_revision').count(),
                'ventas_devueltas': VentaPortabilidad.objects.filter(estado_venta='devuelta').count(),
                'ventas_aprobadas': VentaPortabilidad.objects.filter(estado_venta='aprobada').count(),
                'ventas_digitadas': VentaPortabilidad.objects.filter(estado_venta='digitada').count(),
                'titulo': 'Dashboard Superusuario',
                'ventas_recientes': VentaPortabilidad.objects.select_related('plan_adquiere').all().order_by('-fecha_creacion')[:10]
            })

    return render(request, 'telefonica/dashboard.html', context)

# Gestión de ventas
@login_required
def venta_crear_portabilidad(request, documento=None):
    """Vista para crear una nueva venta de portabilidad.
    
    Si se proporciona un documento en la URL, intenta precargar los datos del cliente.
    Esto permite la integración con sistemas externos como marcadores telefónicos.
    """
    if request.method == 'POST':
        form = VentaPortabilidadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.agente = request.user
            venta.save()
            messages.success(request, 'Venta de portabilidad registrada exitosamente.')
            return redirect('telefonica:detalle_venta_portabilidad', pk=venta.id)
    else:
        initial_data = {'documento': documento} if documento else {}
        form = VentaPortabilidadForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Venta de Portabilidad',
        'tipo_venta': 'portabilidad',
        'subtitulo': 'Complete el formulario para registrar una nueva venta de portabilidad.'
    }
    return render(request, 'telefonica/venta_portabilidad_form.html', context)

@login_required
def venta_crear_prepago(request, documento=None):
    """Vista para crear una nueva venta de Prepago"""
    if request.method == 'POST':
        form = VentaPrePosForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.agente = request.user
            venta.estado_venta = 'pendiente_revision'
            venta.save()
            messages.success(request, 'Venta de Pre a Pos registrada exitosamente.')
            return redirect('telefonica:detalle_venta_prepago', pk=venta.id)
    else:
        initial_data = {}
        if documento:
            initial_data = {'documento': documento}
        form = VentaPrePosForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Venta de Pre a Pos',
        'subtitulo': 'Complete el formulario para registrar una nueva venta de Pre a Pos.'
    }
    return render(request, 'telefonica/venta_prepago_form.html', context)

@login_required
def venta_crear_upgrade(request, documento=None):
    """Vista para crear una nueva venta de Upgrade"""
    if request.method == 'POST':
        form = VentaUpgradeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.agente = request.user
            venta.estado_venta = 'pendiente_revision'
            venta.save()
            messages.success(request, 'Venta de Upgrade registrada exitosamente.')
            return redirect('telefonica:detalle_venta_upgrade', pk=venta.id)
    else:
        initial_data = {}
        if documento:
            initial_data = {'documento': documento}
        form = VentaUpgradeForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Nueva Venta de Upgrade',
        'subtitulo': 'Complete el formulario para registrar una nueva venta de Upgrade.'
    }
    return render(request, 'telefonica/venta_upgrade_form.html', context)

@login_required
def detalle_venta(request, pk):
    """
    Muestra el detalle de una venta y permite su gestión por backoffice.
    Unifica la vista de detalle y gestión.
    """
    venta = get_object_or_404(VentaPortabilidad.objects.select_related('agente', 'backoffice'), pk=pk)
    
    # Determinar roles y permisos
    is_backoffice = request.user.groups.filter(name='backoffice').exists()
    is_asesor = request.user.groups.filter(name='asesor').exists()

    # Un asesor solo puede ver sus propias ventas. Un backoffice puede ver todas.
    if not is_backoffice and (not is_asesor or venta.agente != request.user):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('telefonica:dashboard')

    form = None
    # El formulario de gestión solo se muestra a backoffice y si la venta está pendiente.
    if is_backoffice and venta.estado_venta == 'pendiente_revision':
        if request.method == 'POST':
            form = GestionBackofficeForm(request.POST)
            if form.is_valid():
                gestion = form.save(commit=False)
                gestion.venta = venta
                gestion.gestor = request.user
                
                # Actualizar el estado principal de la venta
                venta.estado_venta = gestion.nuevo_estado
                venta.backoffice = request.user # Asignar el backoffice que gestionó
                
                # Si se devuelve, se copian los campos a corregir a la venta para visibilidad del asesor
                if venta.estado_venta == 'devuelta':
                    venta.campos_a_corregir = gestion.campos_a_corregir
                
                venta.save()
                gestion.save()
                
                messages.success(request, f"La venta #{venta.numero} ha sido actualizada a '{venta.get_estado_venta_display()}'.")
                return redirect('telefonica:detalle_venta', pk=venta.pk)
        else:
            # En GET, se muestra un formulario vacío para la gestión
            form = GestionBackofficeForm()

    # El botón de corregir solo aparece para el asesor dueño de la venta si está devuelta.
    puede_corregir = is_asesor and venta.agente == request.user and venta.estado_venta == 'devuelta'

    context = {
        'venta': venta,
        'form': form, # El formulario de gestión (si aplica)
        'puede_corregir': puede_corregir,
        'gestiones_asesor': venta.gestiones_asesor.all().order_by('-fecha_gestion'),
        'gestiones_backoffice': venta.gestiones_backoffice.all().order_by('-fecha_gestion'),
    }
    
    return render(request, 'telefonica/venta_portabilidad_detalle.html', context)


@login_required
def ventas_lista(request):
    """Lista de ventas de portabilidad con filtrado según el rol del usuario"""
    is_backoffice_user = request.user.groups.filter(name='backoffice').exists()

    # Filtrar ventas según el rol del usuario
    if is_backoffice_user:
        # Backoffice puede ver todas las ventas
        ventas = VentaPortabilidad.objects.all().order_by('-fecha_creacion')
    else:
        # Asesores solo ven sus propias ventas
        ventas = VentaPortabilidad.objects.filter(agente=request.user).order_by('-fecha_creacion')
    
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado')
    if estado:
        ventas = ventas.filter(estado_venta=estado)
    
    # Filtrar por documento si se especifica
    documento = request.GET.get('documento')
    if documento:
        ventas = ventas.filter(documento__icontains=documento)
    
    # Filtrar por fechas
    fecha_desde = request.GET.get('fecha_desde')
    if fecha_desde:
        ventas = ventas.filter(fecha_creacion__gte=fecha_desde)
    
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_hasta:
        from datetime import datetime, timedelta
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
        ventas = ventas.filter(fecha_creacion__lt=fecha_hasta_dt)
    
    paginator = Paginator(ventas, 10)  # 10 ventas por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/ventas_portabilidad_lista.html', {
        'ventas': page_obj,
        'titulo': 'Listado de Ventas de Portabilidad',
        'es_backoffice': is_backoffice_user
    })

@login_required
def venta_detalle(request, pk):
    """
    Vista que redirecciona a la vista específica según el tipo de venta.
    Esta vista existe para mantener compatibilidad con las URLs existentes.
    """
    # Intentar obtener la venta como VentaPortabilidad
    try:
        venta = VentaPortabilidad.objects.get(id=pk)
        return redirect('telefonica:detalle_venta_portabilidad', pk=pk)
    except VentaPortabilidad.DoesNotExist:
        pass
    
    # Intentar obtener la venta como VentaPrePos
    try:
        venta = VentaPrePos.objects.get(id=pk)
        return redirect('telefonica:detalle_venta_prepago', pk=pk)
    except VentaPrePos.DoesNotExist:
        pass
    
    # Si no se encuentra la venta, devolver 404
    raise Http404("No se encontró la venta especificada.")

@login_required
def venta_corregir(request, venta_id):
    """Vista para corregir una venta devuelta"""
    venta = get_object_or_404(VentaPortabilidad, id=venta_id)
    
    # Solo el asesor que creó la venta puede corregirla
    if venta.agente != request.user:
        return HttpResponseForbidden("No tienes permiso para corregir esta venta")
    
    # Solo se pueden corregir ventas devueltas
    if venta.estado_venta != 'devuelta':
        messages.error(request, 'Esta venta no está en estado de corrección')
        return redirect('telefonica:detalle_venta_portabilidad', pk=venta.id)
    
    # Obtener la última gestión de backoffice (motivo de devolución)
    ultima_gestion = GestionBackoffice.objects.filter(
        venta=venta
    ).order_by('-fecha_gestion').first()
    
    if request.method == 'POST':
        form = CorreccionVentaForm(request.POST, request.FILES, instance=venta)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.estado_venta = 'pendiente_revision'  # Vuelve a pendiente de revisión
            venta.save()
            
            # Registrar gestión del asesor
            gestion = GestionAsesor(
                venta=venta,
                agente=request.user,
                comentario='Venta corregida y reenviada a revisión'
            )
            gestion.save()
            
            messages.success(request, 'Venta corregida y reenviada a revisión')
            return redirect('telefonica:detalle_venta_portabilidad', pk=venta.id)
    else:
        form = CorreccionVentaForm(instance=venta)
    
    context = {
        'venta': venta,
        'form': form,
        'ultima_gestion': ultima_gestion,
        'titulo': 'Corregir Venta'
    }
    
    return render(request, 'telefonica/venta_corregir.html', context)
    

# ----- CRUD para Planes de Portabilidad -----

@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists() or u.is_superuser)
def planes_portabilidad_lista(request):
    """Lista todos los planes de portabilidad disponibles"""
    # Filtrar planes según estado si se especifica
    estado = request.GET.get('estado')
    if estado:
        planes = Planes_portabilidad.objects.filter(estado=estado).order_by('-fecha_creacion')
    else:
        planes = Planes_portabilidad.objects.all().order_by('-fecha_creacion')
    
    paginator = Paginator(planes, 10)  # 10 planes por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/planes_portabilidad_lista.html', {
        'planes': page_obj,
        'titulo': 'Planes de Portabilidad',
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists() or u.is_superuser)
def plan_portabilidad_crear(request):
    """Crea un nuevo plan de portabilidad"""
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan {plan.nombre_plan} creado correctamente.')
            return redirect('telefonica:planes_portabilidad_lista')
    else:
        form = PlanesPortabilidadForm()
    
    return render(request, 'telefonica/plan_portabilidad_form.html', {
        'form': form,
        'titulo': 'Crear Plan de Portabilidad',
        'accion': 'Crear'
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists() or u.is_superuser)
def plan_portabilidad_editar(request, plan_id):
    """Edita un plan de portabilidad existente"""
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan {plan.nombre_plan} actualizado correctamente.')
            return redirect('telefonica:planes_portabilidad_lista')
    else:
        form = PlanesPortabilidadForm(instance=plan)
    
    return render(request, 'telefonica/plan_portabilidad_form.html', {
        'form': form,
        'plan': plan,
        'titulo': 'Editar Plan de Portabilidad',
        'accion': 'Actualizar'
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists() or u.is_superuser)
def plan_portabilidad_eliminar(request, plan_id):
    """Elimina un plan de portabilidad"""
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    if request.method == 'POST':
        nombre_plan = plan.nombre_plan
        plan.delete()
        messages.success(request, f'Plan {nombre_plan} eliminado correctamente.')
        return redirect('telefonica:planes_portabilidad_lista')
    
    return render(request, 'telefonica/plan_portabilidad_confirmar_eliminar.html', {
        'plan': plan,
        'titulo': 'Eliminar Plan de Portabilidad'
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists() or u.is_superuser)
@csrf_exempt  # Eximir de la protección CSRF para peticiones AJAX
def plan_portabilidad_cambiar_estado(request, plan_id):
    """Cambia el estado de un plan de portabilidad (activar/desactivar)"""
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    # Cambiar el estado del plan
    if plan.estado == 'activo':
        plan.estado = 'inactivo'
        mensaje = f'Plan {plan.nombre_plan} desactivado correctamente.'
    else:
        plan.estado = 'activo'
        mensaje = f'Plan {plan.nombre_plan} activado correctamente.'
    
    plan.save()
    messages.success(request, mensaje)
    
    # Si es una solicitud AJAX, devolver respuesta JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'mensaje': mensaje, 'estado': plan.estado})
    
    return redirect('telefonica:planes_portabilidad_lista')

@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists())
def venta_revisar(request, venta_id):
    """Vista para que backoffice revise una venta"""
    venta = get_object_or_404(VentaPortabilidad, id=venta_id)
    
    # Solo se pueden revisar ventas pendientes
    if venta.estado_venta != 'pendiente_revision':
        messages.error(request, 'Esta venta ya ha sido revisada')
        return redirect('telefonica:venta_detalle', venta_id=venta.id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        comentario = request.POST.get('comentario')
        
        if accion not in ['aprobar', 'devolver']:
            messages.error(request, 'Acción no válida')
            return redirect('telefonica:venta_revisar', venta_id=venta.id)
        
        # Actualizar estado de la venta
        if accion == 'aprobar':
            venta.estado_venta = 'aprobada'
            mensaje = 'Venta aprobada correctamente'
        else:  # devolver
            venta.estado_venta = 'devuelta'
            mensaje = 'Venta devuelta para corrección'
        
        venta.save()
        
        # Registrar gestión de backoffice
        gestion = GestionBackoffice(
            venta=venta,
            usuario=request.user,
            accion=accion,
            comentario=comentario
        )
        gestion.save()
        
        messages.success(request, mensaje)
        return redirect('telefonica:ventas_pendientes')
    
    return render(request, 'telefonica/venta_revisar.html', {
        'venta': venta,
        'titulo': 'Revisar Venta'
    })

@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists())
def ventas_pendientes(request):
    """Bandeja de ventas pendientes de revisión"""
    ventas = VentaPortabilidad.objects.filter(estado_venta='pendiente_revision').order_by('-fecha_creacion')
    
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/bandeja_pendientes.html', {
        'page_obj': page_obj,
        'titulo': 'Bandeja de Ventas Pendientes'
    })

@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists())
def bandeja_digitacion(request):
    """Bandeja de ventas aprobadas pendientes de digitación"""
    if not es_backoffice(request.user):
        messages.error(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    ventas = VentaPortabilidad.objects.filter(estado_venta='aprobada').order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(ventas, 10)  # 10 ventas por página
    page = request.GET.get('page')
    ventas_paginadas = paginator.get_page(page)
    
    context = {
        'ventas': ventas_paginadas,
        'titulo': 'Bandeja de Digitación',
        'subtitulo': 'Ventas aprobadas pendientes de digitación',
        'total': ventas.count(),
    }
    
    return render(request, 'telefonica/bandeja_generica.html', context)

@login_required
def bandeja_seguimiento(request):
    """
    Vista que muestra todas las ventas para hacer seguimiento
    """
    is_backoffice = request.user.groups.filter(name='backoffice').exists()
    is_asesor = request.user.groups.filter(name='asesor').exists()

    # Verificar permisos
    if not is_backoffice and not is_asesor:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener ventas según el rol
    if is_backoffice:
        # Backoffice puede ver todas las ventas
        ventas = VentaPortabilidad.objects.all().order_by('-fecha_creacion')
    else: # is_asesor
        # Asesor solo puede ver sus ventas
        ventas = VentaPortabilidad.objects.filter(agente=request.user).order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(ventas, 10)
    page = request.GET.get('page')
    ventas_paginadas = paginator.get_page(page)
    
    context = {
        'ventas': ventas_paginadas,
        'titulo': 'Seguimiento de Ventas',
        'subtitulo': 'Control y seguimiento de todas las ventas',
        'total': ventas.count(),
    }
    
    return render(request, 'telefonica/bandeja_generica.html', context)

@login_required
def bandeja_devueltas(request):
    """
    Vista que muestra las ventas devueltas para corrección
    """
    is_backoffice = request.user.groups.filter(name='backoffice').exists()
    is_asesor = request.user.groups.filter(name='asesor').exists()

    # Verificar permisos según rol
    if is_backoffice:
        # Backoffice ve todas las ventas devueltas
        ventas = VentaPortabilidad.objects.filter(estado_venta='devuelta').order_by('-fecha_creacion')
    elif is_asesor:
        # Asesor solo ve sus ventas devueltas
        ventas = VentaPortabilidad.objects.filter(
            agente=request.user,
            estado_venta='devuelta'
        ).order_by('-fecha_creacion')
    else:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Paginación
    paginator = Paginator(ventas, 10)
    page = request.GET.get('page')
    ventas_paginadas = paginator.get_page(page)
    
    context = {
        'ventas': ventas_paginadas,
        'titulo': 'Ventas Devueltas',
        'subtitulo': 'Ventas que requieren corrección',
        'total': ventas.count(),
    }
    
    return render(request, 'telefonica/bandeja_generica.html', context)

@login_required
def bandeja_asesores(request):
    """Bandeja de ventas en seguimiento"""
    if es_backoffice(request.user): 
        ventas = VentaPortabilidad.objects.filter(estado_venta__in=['digitada', 'completada']).order_by('-fecha_creacion')
    else:
        ventas = VentaPortabilidad.objects.filter(
            agente=request.user, 
            estado_venta__in=['digitada', 'completada']
        ).order_by('-fecha_creacion')
    
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/bandeja_seguimiento.html', {
        'page_obj': page_obj,
        'titulo': 'Bandeja de Seguimiento',
        'es_backoffice': es_backoffice(request.user)
    })

@login_required
def bandeja_devueltas(request):
    """Bandeja de ventas devueltas para corrección"""
    if es_backoffice(request.user):
        ventas = VentaPortabilidad.objects.filter(estado_venta='devuelta').order_by('-fecha_creacion')
    else:
        ventas = VentaPortabilidad.objects.filter(
            agente=request.user,
            estado_venta='devuelta'
        ).order_by('-fecha_creacion')
    
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/bandeja_devueltas.html', {
        'page_obj': page_obj,
        'titulo': 'Bandeja de Ventas Devueltas',
        'es_backoffice': es_backoffice(request.user)
    })

@login_required
@user_passes_test(lambda u: u.groups.filter(name='backoffice').exists())
def comisiones_calcular(request):
    """Vista para calcular comisiones de ventas aprobadas"""
    if request.method == 'POST':
        ventas_ids = request.POST.getlist('ventas_ids')
        ventas = VentaPortabilidad.objects.filter(id__in=ventas_ids, estado_venta='aprobada')
        
        contador = 0
        for venta in ventas:
            # Verificar si ya existe una comisión para esta venta
            if not Comision.objects.filter(venta=venta).exists():
                # Aquí se implementaría la lógica de cálculo según el tipo de plan, segmento, etc.
                # Por ahora usamos un valor fijo de ejemplo
                valor_comision = 30000  # Valor fijo de ejemplo
                
                # Crear registro de comisión
                comision = Comision(
                    venta=venta,
                    agente=venta.agente,
                    valor=valor_comision,
                    estado='calculada'
                )
                comision.save()
                contador += 1
        
        messages.success(request, f"Se calcularon {contador} nuevas comisiones")
        return redirect('telefonica:comisiones')
    
    # Obtener ventas aprobadas sin comisión calculada
    ventas = VentaPortabilidad.objects.filter(
        estado_venta='aprobada'
    ).exclude(
        id__in=Comision.objects.values_list('venta_id', flat=True)
    ).order_by('-fecha_creacion')
    
    return render(request, 'telefonica/comisiones_calcular.html', {
        'ventas': ventas,
        'titulo': 'Calcular Comisiones'
    })

@login_required
def comisiones_lista(request):
    """Lista de comisiones"""
    is_backoffice = request.user.groups.filter(name='backoffice').exists()

    if is_backoffice:
        comisiones = Comision.objects.all().order_by('-fecha_calculo')
    else:
        comisiones = Comision.objects.filter(agente=request.user).order_by('-fecha_calculo')
    
    paginator = Paginator(comisiones, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/comisiones_lista.html', {
        'page_obj': page_obj,
        'titulo': 'Comisiones',
        'es_backoffice': is_backoffice
    })

@login_required
def comision_detalle(request, comision_id):
    """Vista para mostrar el detalle de una comisión"""
    comision = get_object_or_404(Comision, id=comision_id)
    
    # Verificar permisos (Backoffice puede ver todas, Asesores solo las propias)
    if not es_backoffice(request.user) and comision.agente != request.user:
        return HttpResponseForbidden("No tienes permiso para ver esta comisión")
    
    # Gestionar el formulario si es Backoffice y es POST
    if request.method == 'POST' and es_backoffice(request.user):
        # Actualizar los campos de la comisión
        comision.estado = request.POST.get('estado')
        comision.fecha_pago = request.POST.get('fecha_pago')
        comision.observaciones = request.POST.get('observaciones')
        comision.save()
        messages.success(request, 'Comisión actualizada correctamente')
        return redirect('telefonica:comision_detalle', comision_id=comision.id)
    
    # Preparar datos para la plantilla
    context = {
        'comision': comision,
        'es_backoffice': es_backoffice(request.user),
    }
    
    return render(request, 'telefonica/comisiones_detalle.html', context)

# Vista para servir el fragmento de menú lateral
@login_required
def menu_fragment(request):
    """
    Vista que retorna el fragmento HTML del menú lateral de Telefónica.
    Esta vista es consumida por el script de integración mediante fetch.
    """
    # Verificar si el usuario pertenece a alguno de los grupos de Telefónica
    groups = request.user.groups.all().values_list('name', flat=True)
    telefonica_groups = ['asesor', 'backoffice']
    
    # Solo mostrar el menú si el usuario pertenece a alguno de los grupos de Telefónica
    if not any(group in telefonica_groups for group in groups):
        return HttpResponse("")
    
    # Renderizar el fragmento de menú
    html = render_to_string('telefonica/includes/sidebar_menu.html', {
        'user': request.user,
    })
    
    return HttpResponse(html)

# Vistas de bandejas de trabajo
@login_required
def bandeja_pendientes(request):
    """
    Vista que muestra las ventas pendientes de revisión para los usuarios de Backoffice
    """
    # Verificar permisos
    if not request.user.groups.filter(name='backoffice').exists():
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener ventas pendientes de revisión
    ventas = VentaPortabilidad.objects.filter(estado_venta='pendiente_revision').order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(ventas, 10)  # 10 ventas por página
    page = request.GET.get('page')
    ventas_paginadas = paginator.get_page(page)
    
    context = {
        'ventas': ventas_paginadas,
        'titulo': 'Bandeja de Pendientes',
        'subtitulo': 'Ventas pendientes de revisión',
        'total': ventas.count(),
    }
    
    return render(request, 'telefonica/bandeja_generica.html', context)


@login_required
def perfil_telefonica(request):
    """
    Vista para que los usuarios del módulo Telefónica puedan ver y editar su perfil.
    """
    user = request.user
    if request.method == 'POST':
        # Procesar datos del formulario
        nombre = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Actualizar nombre y apellidos
        if nombre:
            user.first_name = nombre
        if apellidos:
            user.last_name = apellidos
        
        # Gestionar cambio de contraseña
        if password1:
            if password1 == password2:
                user.set_password(password1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Tu perfil y contraseña han sido actualizados.')
            else:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('telefonica:perfil')
        else:
            user.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')

        return redirect('telefonica:perfil')

    return render(request, 'telefonica/perfil_telefonica.html', {'user': user})


# Vistas para la gestión de planes de portabilidad
@login_required
def planes_lista(request):
    """
    Vista que muestra la lista de planes de portabilidad disponibles.
    Solo accesible para administradores.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener todos los planes ordenados por nombre
    planes = Planes_portabilidad.objects.all().order_by('nombre_plan')
    
    # Paginación
    paginator = Paginator(planes, 10)  # 10 planes por página
    page = request.GET.get('page')
    planes_paginados = paginator.get_page(page)
    
    context = {
        'planes': planes_paginados,
        'titulo': 'Gestión de Planes',
        'subtitulo': 'Planes disponibles para ventas',
        'total': planes.count(),
    }
    
    return render(request, 'telefonica/planes/planes_lista.html', context)


@login_required
def plan_crear(request):
    """
    Vista para crear un nuevo plan de portabilidad.
    Solo accesible para administradores.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan {plan.nombre_plan} creado correctamente')
            return redirect('telefonica:planes_lista')
    else:
        form = PlanesPortabilidadForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Plan',
        'subtitulo': 'Añadir nuevo plan de portabilidad',
        'boton': 'Crear Plan',
    }
    
    return render(request, 'telefonica/planes/plan_form.html', context)


@login_required
def plan_editar(request, plan_id):
    """
    Vista para editar un plan de portabilidad existente.
    Solo accesible para administradores.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener el plan o devolver 404
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan {plan.nombre_plan} actualizado correctamente')
            return redirect('telefonica:planes_lista')
    else:
        form = PlanesPortabilidadForm(instance=plan)
    
    context = {
        'form': form,
        'plan': plan,
        'titulo': 'Editar Plan',
        'subtitulo': f'Modificar plan: {plan.nombre_plan}',
        'boton': 'Guardar Cambios',
    }
    
    return render(request, 'telefonica/planes/plan_form.html', context)


@login_required
def plan_detalle(request, plan_id):
    """
    Vista para ver el detalle de un plan de portabilidad.
    Solo accesible para administradores.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener el plan o devolver 404
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    # Obtener las ventas asociadas a este plan
    ventas = plan.ventas.all().order_by('-fecha_creacion')[:10]  # Mostrar solo las 10 más recientes
    
    context = {
        'plan': plan,
        'ventas': ventas,
        'titulo': 'Detalle de Plan',
        'subtitulo': f'Plan: {plan.nombre_plan}',
        'total_ventas': plan.ventas.count(),
    }
    
    return render(request, 'telefonica/planes/plan_detalle.html', context)


@login_required
def plan_eliminar(request, plan_id):
    """
    Vista para eliminar un plan de portabilidad.
    Solo accesible para administradores.
    Utiliza confirmación por POST para evitar eliminaciones accidentales.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener el plan o devolver 404
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    # Verificar si el plan tiene ventas asociadas
    if plan.ventas.exists():
        messages.error(request, f'No se puede eliminar el plan {plan.nombre_plan} porque tiene ventas asociadas')
        return redirect('telefonica:plan_detalle', plan_id=plan.id)
    
    if request.method == 'POST':
        nombre_plan = plan.nombre_plan
        plan.delete()
        messages.success(request, f'Plan {nombre_plan} eliminado correctamente')
        return redirect('telefonica:planes_lista')
    
    context = {
        'plan': plan,
        'titulo': 'Eliminar Plan',
        'subtitulo': f'¿Estás seguro de eliminar el plan {plan.nombre_plan}?',
    }
    
    return render(request, 'telefonica/planes/plan_confirmar_eliminacion.html', context)


@login_required
def plan_cambiar_estado(request, plan_id):
    """
    Vista para cambiar rápidamente el estado de un plan (activo/inactivo).
    Solo accesible para administradores.
    Requiere petición POST.
    """
    # Verificar que el usuario es administrador
    if not request.user.is_superuser:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Verificar que sea una petición POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtener el plan o devolver 404
    plan = get_object_or_404(Planes_portabilidad, id=plan_id)
    
    # Cambiar el estado
    nuevo_estado = 'inactivo' if plan.estado == 'activo' else 'activo'
    plan.estado = nuevo_estado
    plan.save()
    
    return JsonResponse({
        'success': True,
        'nuevo_estado': nuevo_estado,
        'mensaje': f'Estado del plan {plan.nombre_plan} cambiado a {nuevo_estado}'
    })


# CRUD para Planes de Portabilidad
@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='backoffice').exists())
def planes_portabilidad_lista(request):
    """
    Vista para listar los planes de portabilidad con filtros y paginación.
    Solo accesible para usuarios con rol backoffice o superusuarios.
    """
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado', '')
    planes = Planes_portabilidad.objects.all().order_by('-fecha_creacion')
    
    if estado:
        planes = planes.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(planes, 9)  # 9 planes por página para mostrar en grid de 3x3
    page = request.GET.get('page')
    try:
        planes = paginator.page(page)
    except PageNotAnInteger:
        planes = paginator.page(1)
    except EmptyPage:
        planes = paginator.page(paginator.num_pages)
    
    return render(request, 'telefonica/planes_portabilidad_lista.html', {
        'planes': planes,
        'titulo': 'Planes de Portabilidad',
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='backoffice').exists())
def plan_portabilidad_crear(request):
    """
    Vista para crear un nuevo plan de portabilidad.
    Solo accesible para usuarios con rol backoffice o superusuarios.
    """
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan de portabilidad "{plan.nombre_plan}" creado correctamente.')
            return redirect('telefonica:planes_portabilidad_lista')
    else:
        form = PlanesPortabilidadForm()
    
    return render(request, 'telefonica/plan_portabilidad_form.html', {
        'form': form,
        'titulo': 'Crear Plan de Portabilidad',
        'accion': 'Crear Plan'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='backoffice').exists())
def plan_portabilidad_editar(request, plan_id):
    """
    Vista para editar un plan de portabilidad existente.
    Solo accesible para usuarios con rol backoffice o superusuarios.
    """
    plan = get_object_or_404(Planes_portabilidad, pk=plan_id)
    
    if request.method == 'POST':
        form = PlanesPortabilidadForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan de portabilidad "{plan.nombre_plan}" actualizado correctamente.')
            return redirect('telefonica:planes_portabilidad_lista')
    else:
        form = PlanesPortabilidadForm(instance=plan)
    
    return render(request, 'telefonica/plan_portabilidad_form.html', {
        'form': form,
        'plan': plan,
        'titulo': 'Editar Plan de Portabilidad',
        'accion': 'Guardar Cambios'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='backoffice').exists())
def plan_portabilidad_eliminar(request, plan_id):
    """
    Vista para eliminar un plan de portabilidad.
    Solo accesible para usuarios con rol backoffice o superusuarios.
    """
    plan = get_object_or_404(Planes_portabilidad, pk=plan_id)
    
    if request.method == 'POST':
        nombre_plan = plan.nombre_plan
        plan.delete()
        messages.success(request, f'Plan de portabilidad "{nombre_plan}" eliminado correctamente.')
        return redirect('telefonica:planes_portabilidad_lista')
    
    return render(request, 'telefonica/plan_portabilidad_confirmar_eliminar.html', {
        'plan': plan
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='backoffice').exists())
def plan_portabilidad_cambiar_estado(request, plan_id):
    """
    Vista para cambiar el estado de un plan de portabilidad mediante AJAX.
    Solo accesible para usuarios con rol backoffice o superusuarios.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        plan = get_object_or_404(Planes_portabilidad, pk=plan_id)
        
        # Cambiar el estado (alternar entre activo e inactivo)
        nuevo_estado = 'inactivo' if plan.estado == 'activo' else 'activo'
        plan.estado = nuevo_estado
        plan.save()
        
        mensaje = f'Plan "{plan.nombre_plan}" {"activado" if nuevo_estado == "activo" else "desactivado"} correctamente.'
        
        return JsonResponse({
            'success': True,
            'estado': nuevo_estado,
            'mensaje': mensaje
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def detalle_venta_portabilidad(request, pk):
    """
    Vista para mostrar el detalle de una venta de portabilidad.
    
    Permite ver todos los datos de la venta, incluyendo el historial de gestiones
    y realizar acciones según el rol del usuario.
    """
    # Obtener la venta o devolver 404 si no existe
    venta = get_object_or_404(VentaPortabilidad, pk=pk)
    
    # Verificar permisos: el usuario debe ser el agente de la venta, un backoffice o un superusuario
    user = request.user
    es_backoffice = user.groups.filter(name__iexact='backoffice').exists()
    es_propietario = (venta.agente == user)
    
    if not (es_propietario or es_backoffice or user.is_superuser):
        return HttpResponseForbidden("No tienes permisos para ver esta venta.")
    
    # Obtener historial de gestiones (VentaPrePos no tiene gestiones por ahora)
    gestiones_asesor = []
    gestiones_backoffice = []
    
    # Formularios para añadir gestiones
    gestion_asesor_form = GestionAsesorForm()
    gestion_backoffice_form = GestionBackofficeForm() if es_backoffice or user.is_superuser else None
    
    context = {
        'venta': venta,
        'gestiones_asesor': gestiones_asesor,
        'gestiones_backoffice': gestiones_backoffice,
        'gestion_asesor_form': gestion_asesor_form,
        'gestion_backoffice_form': gestion_backoffice_form,
        'es_backoffice': es_backoffice,
        'es_propietario': es_propietario,
    }
    
    return render(request, 'telefonica/venta_detalle_portabilidad.html', context)


@login_required
def detalle_venta_prepago(request, pk):
    """
    Vista para mostrar el detalle de una venta de prepago.
    
    Permite ver todos los datos de la venta, incluyendo el historial de gestiones
    y realizar acciones según el rol del usuario.
    """
    # Obtener la venta o devolver 404 si no existe
    venta = get_object_or_404(VentaPrePos, pk=pk)
    
    # Verificar permisos: el usuario debe ser el agente de la venta, un backoffice o un superusuario
    user = request.user
    es_backoffice = user.groups.filter(name__iexact='backoffice').exists()
    es_propietario = (venta.agente == user)
    
    if not (es_propietario or es_backoffice or user.is_superuser):
        return HttpResponseForbidden("No tienes permisos para ver esta venta.")
    
    # Procesar formularios (gestiones no implementadas para VentaPrePos)
    if request.method == 'POST':
        messages.info(request, 'Las gestiones para ventas PrePos aún no están implementadas.')
    
    # Obtener historial de gestiones (VentaPrePos no tiene gestiones por ahora)
    gestiones_asesor = []
    gestiones_backoffice = []
    
    # Formularios para añadir gestiones
    gestion_asesor_form = GestionAsesorForm()
    gestion_backoffice_form = GestionBackofficeForm() if es_backoffice or user.is_superuser else None
    
    context = {
        'venta': venta,
        'gestiones_asesor': gestiones_asesor,
        'gestiones_backoffice': gestiones_backoffice,
        'gestion_asesor_form': gestion_asesor_form,
        'gestion_backoffice_form': gestion_backoffice_form,
        'es_backoffice': es_backoffice,
        'es_propietario': es_propietario,
    }
    
    return render(request, 'telefonica/venta_detalle_prepago.html', context)


@login_required
def detalle_venta_upgrade(request, pk):
    """
    Vista para mostrar el detalle de una venta de upgrade.
    
    Permite ver todos los datos de la venta, incluyendo el historial de gestiones
    y realizar acciones según el rol del usuario.
    """
    # Obtener la venta o devolver 404 si no existe
    venta = get_object_or_404(VentaUpgrade, pk=pk)
    
    # Verificar permisos: el usuario debe ser el agente de la venta, un backoffice o un superusuario
    user = request.user
    es_backoffice = user.groups.filter(name__iexact='backoffice').exists()
    es_propietario = (venta.agente == user)
    
    if not (es_propietario or es_backoffice or user.is_superuser):
        return HttpResponseForbidden("No tienes permisos para ver esta venta.")
    
    # Procesar formularios (gestiones no implementadas para VentaUpgrade)
    if request.method == 'POST':
        messages.info(request, 'Las gestiones para ventas Upgrade aún no están implementadas.')
    
    # Obtener historial de gestiones (VentaUpgrade no tiene gestiones por ahora)
    gestiones_asesor = []
    gestiones_backoffice = []
    
    # Formularios para añadir gestiones
    gestion_asesor_form = GestionAsesorForm()
    gestion_backoffice_form = GestionBackofficeForm() if es_backoffice or user.is_superuser else None
    
    context = {
        'venta': venta,
        'gestiones_asesor': gestiones_asesor,
        'gestiones_backoffice': gestiones_backoffice,
        'gestion_asesor_form': gestion_asesor_form,
        'gestion_backoffice_form': gestion_backoffice_form,
        'es_backoffice': es_backoffice,
        'es_propietario': es_propietario,
    }
    
    return render(request, 'telefonica/venta_detalle_upgrade.html', context)