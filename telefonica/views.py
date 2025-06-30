from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import Cliente, Venta, GestionAsesor, GestionBackoffice, Comision
from .forms import (
    ClienteForm, VentaForm, VentaClienteForm, 
    GestionAsesorForm, GestionBackofficeForm, CorreccionVentaForm
)

# Funciones auxiliares para verificar permisos
def es_backoffice(user):
    return user.groups.filter(name='Backoffice').exists() or user.is_superuser

def es_asesor(user):
    return user.groups.filter(name='Asesores').exists() or user.is_superuser

# Vistas principales
@login_required
def dashboard(request):
    """Vista de dashboard adaptada según el rol del usuario"""
    if es_backoffice(request.user):
        # Estadísticas para backoffice
        ventas_pendientes = Venta.objects.filter(estado_revisado='pendiente_revision').count()
        ventas_devueltas = Venta.objects.filter(estado_revisado='devuelta').count()
        ventas_aprobadas = Venta.objects.filter(estado_revisado='aprobada').count()
        ventas_digitadas = Venta.objects.filter(estado_revisado='digitada').count()
        
        # Ventas recientes para backoffice (pendientes de revisión)
        ventas_recientes = Venta.objects.filter(
            estado_revisado='pendiente_revision'
        ).order_by('-fecha_creacion')[:10]
        
        context = {
            'ventas_pendientes': ventas_pendientes,
            'ventas_devueltas': ventas_devueltas,
            'ventas_aprobadas': ventas_aprobadas,
            'ventas_digitadas': ventas_digitadas,
            'ventas_recientes': ventas_recientes,
            'es_backoffice': True,
            'es_asesor': False,
            'titulo': 'Dashboard Backoffice'
        }
    else:
        # Estadísticas para asesores
        mis_ventas = Venta.objects.filter(agente=request.user).count()
        mis_ventas_pendientes = Venta.objects.filter(
            agente=request.user, 
            estado_revisado='pendiente_revision'
        ).count()
        mis_ventas_devueltas = Venta.objects.filter(
            agente=request.user, 
            estado_revisado='devuelta'
        ).count()
        
        # Comisiones pendientes
        mis_comisiones_pendientes = Comision.objects.filter(
            agente=request.user, 
            estado='pendiente'
        ).count()
        
        # Ventas recientes para el asesor
        ventas_recientes = Venta.objects.filter(
            agente=request.user
        ).order_by('-fecha_creacion')[:10]
        
        context = {
            'mis_ventas': mis_ventas,
            'mis_ventas_pendientes': mis_ventas_pendientes,
            'mis_ventas_devueltas': mis_ventas_devueltas,
            'mis_comisiones_pendientes': mis_comisiones_pendientes,
            'ventas_recientes': ventas_recientes,
            'es_asesor': True,
            'es_backoffice': False,
            'titulo': 'Dashboard Asesor'
        }
    
    # Usar la plantilla dashboard.html que extiende de base_telefonica.html
    return render(request, 'telefonica/dashboard.html', context)

# Gestión de ventas
@login_required
@user_passes_test(es_backoffice)
def venta_gestionar(request, pk):
    """
    Vista para gestionar una venta (aprobar, devolver, digitar, rechazar)
    Esta vista es exclusiva para usuarios del grupo Backoffice
    """
    venta = get_object_or_404(Venta, pk=pk)
    
    if request.method == 'POST':
        form = GestionBackofficeForm(request.POST)
        if form.is_valid():
            gestion = form.save(commit=False)
            gestion.venta = venta
            gestion.usuario = request.user
            gestion.fecha = timezone.now()
            gestion.save()
            
            # Mensaje de éxito según la acción realizada
            mensaje = "Venta gestionada correctamente. "
            if gestion.estado == 'aprobada':
                mensaje += "La venta ha sido aprobada y se ha generado la comisión correspondiente."
            elif gestion.estado == 'devuelta':
                mensaje += "La venta ha sido devuelta al asesor para corrección."
            elif gestion.estado == 'digitada':
                mensaje += "La venta ha sido marcada como digitada en el sistema."
            elif gestion.estado == 'rechazada':
                mensaje += "La venta ha sido rechazada."
                
            messages.success(request, mensaje)
            return redirect('telefonica:venta_detalle', pk=venta.pk)
    else:
        form = GestionBackofficeForm()
    
    context = {
        'venta': venta,
        'form': form,
        'cliente': venta.cliente,
        'titulo': f'Gestionar Venta #{venta.id}'
    }
    
    return render(request, 'telefonica/venta_gestionar.html', context)

@login_required
def venta_crear(request, documento=None):
    """Vista para crear una nueva venta
    
    Si se proporciona un documento en la URL, intenta precargar los datos del cliente.
    Esto permite la integración con sistemas externos como marcadores telefónicos.
    """
    if documento:
        try:
            cliente = Cliente.objects.get(documento=documento)
            initial_data = {
                'documento': cliente.documento,
                'tipo_documento': cliente.tipo_documento,
                'nombres': cliente.nombres,
                'apellidos': cliente.apellidos,
                'correo': cliente.correo,
                'departamento': cliente.departamento,
                'ciudad': cliente.ciudad,
                'barrio': cliente.barrio,
                'direccion': cliente.direccion,
                'telefono': cliente.telefono,
            }
        except Cliente.DoesNotExist:
            initial_data = {}
    else:
        initial_data = {}
    
    if request.method == 'POST':
        form = VentaClienteForm(request.POST, request.FILES)
        if form.is_valid():
            # Procesar los datos del cliente primero
            cliente_data = {
                'documento': form.cleaned_data['documento'],
                'tipo_documento': form.cleaned_data['tipo_documento'],
                'nombres': form.cleaned_data['nombres'],
                'apellidos': form.cleaned_data['apellidos'],
                'correo': form.cleaned_data['correo'],
                'departamento': form.cleaned_data['departamento'],
                'ciudad': form.cleaned_data['ciudad'],
                'barrio': form.cleaned_data['barrio'],
                'direccion': form.cleaned_data['direccion'],
                'telefono': form.cleaned_data['telefono'],
            }
            
            # Buscar si el cliente ya existe por tipo y documento
            try:
                cliente = Cliente.objects.filter(
                    tipo_documento=cliente_data['tipo_documento'],
                    documento=cliente_data['documento']
                ).first()
                
                # Si el cliente no existe, crearlo
                if not cliente:
                    cliente = Cliente(**cliente_data)
                    cliente.save()
                    
                # IMPORTANTE: No actualizamos los datos del cliente si ya existe
                # Esto permite que un cliente tenga varias ventas independientes
                
            except Exception as e:
                messages.error(request, f'Error al procesar el cliente: {str(e)}')
                return redirect('telefonica:venta_crear')
            
            try:
                # Crear nueva venta - NO podemos usar form.save() porque el modelo del form es Cliente
                venta = Venta(
                    cliente=cliente,
                    agente=request.user,
                    estado_revisado='pendiente_revision',
                    tipo_cliente=form.cleaned_data['tipo_cliente'],
                    plan_adquiere=form.cleaned_data['plan_adquiere'],
                    segmento=form.cleaned_data['segmento'],
                    numero_contacto=form.cleaned_data['numero_contacto'],
                    imei=form.cleaned_data['imei'],
                    fvc=form.cleaned_data['fvc'],
                    fecha_entrega=form.cleaned_data['fecha_entrega'],
                    fecha_expedicion=form.cleaned_data['fecha_expedicion'],
                    origen=form.cleaned_data['origen'],
                    numero_grabacion=form.cleaned_data['numero_grabacion'],
                    selector=form.cleaned_data['selector'],
                    orden=form.cleaned_data['orden'],
                    observacion=form.cleaned_data['observacion'],
                    nip=form.cleaned_data['nip']
                )
                
                # Manejar el archivo de confronta si existe
                if 'confronta' in request.FILES:
                    venta.confronta = request.FILES['confronta']
                    
                venta.save()
                
                # Crear una gestión del asesor para esta venta
                gestion_asesor = GestionAsesor(
                    venta=venta,
                    agente=request.user,
                    estado='pendiente_revision',
                    comentario="Venta creada correctamente."
                )
                gestion_asesor.save()
                
                messages.success(request, 'Venta registrada correctamente, pendiente de revisión')
                return redirect('telefonica:ventas_lista')
                
            except Exception as e:
                messages.error(request, f'Error al guardar la venta: {str(e)}')
                return redirect('telefonica:venta_crear')
    else:
        # Usar initial_data para precargar el formulario si hay documento
        form = VentaClienteForm(initial=initial_data)
    
    return render(request, 'telefonica/venta_crear.html', {
        'form': form,
        'titulo': 'Registrar Nueva Venta',
        'cliente_precargado': True if documento else False
    })

@login_required
def detalle_venta(request, pk):
    """Vista para mostrar detalles de una venta específica"""
    # Obtener la venta o devolver 404 si no existe
    venta = get_object_or_404(Venta, pk=pk)
    
    # Obtener gestiones relacionadas con esta venta
    gestiones_asesor = venta.gestiones_asesor.all().order_by('-fecha_gestion')
    gestiones_backoffice = venta.gestiones_backoffice.all().order_by('-fecha_gestion')
    
    # Verificar permisos
    puede_editar = es_asesor(request.user) and venta.estado_revisado == 'devuelta'
    puede_gestionar = es_backoffice(request.user)
    
    context = {
        'venta': venta,
        'gestiones_asesor': gestiones_asesor,
        'gestiones_backoffice': gestiones_backoffice,
        'puede_editar': puede_editar,
        'puede_gestionar': puede_gestionar,
        'es_asesor': es_asesor(request.user),
        'es_backoffice': es_backoffice(request.user),
        'titulo': f'Venta #{venta.numero}'
    }
    
    return render(request, 'telefonica/venta_detalle.html', context)


@login_required
def ventas_lista(request):
    """Lista de ventas con filtrado según el rol del usuario"""
    # Filtrar ventas según el rol del usuario
    if es_backoffice(request.user):
        # Backoffice puede ver todas las ventas
        ventas = Venta.objects.all().order_by('-fecha_creacion')
    else:
        # Asesores solo ven sus propias ventas
        ventas = Venta.objects.filter(agente=request.user).order_by('-fecha_creacion')
    
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado')
    if estado:
        ventas = ventas.filter(estado_revisado=estado)
    
    paginator = Paginator(ventas, 25)  # 25 ventas por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/ventas_lista.html', {
        'page_obj': page_obj,
        'titulo': 'Listado de Ventas',
        'es_backoffice': es_backoffice(request.user)
    })

@login_required
def venta_detalle(request, venta_id):
    """Vista detallada de una venta específica"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Verificar permisos (backoffice puede ver todas, asesores solo las propias)
    if not es_backoffice(request.user) and venta.agente != request.user:
        return HttpResponseForbidden("No tienes permiso para ver esta venta")
    
    # Obtener gestiones asociadas
    gestiones_asesor = GestionAsesor.objects.filter(venta=venta).order_by('-fecha')
    gestiones_backoffice = GestionBackoffice.objects.filter(venta=venta).order_by('-fecha')
    
    # Crear formulario para nueva gestión según el rol
    if es_backoffice(request.user):
        if request.method == 'POST' and 'gestion_backoffice' in request.POST:
            gestion_form = GestionBackofficeForm(request.POST)
            if gestion_form.is_valid():
                gestion = gestion_form.save(commit=False)
                gestion.venta = venta
                gestion.usuario = request.user
                gestion.save()
                messages.success(request, 'Gestión registrada correctamente')
                return redirect('telefonica:venta_detalle', venta_id=venta.id)
        else:
            gestion_form = GestionBackofficeForm()
    else:
        if request.method == 'POST' and 'gestion_asesor' in request.POST:
            gestion_form = GestionAsesorForm(request.POST)
            if gestion_form.is_valid():
                gestion = gestion_form.save(commit=False)
                gestion.venta = venta
                gestion.asesor = request.user
                gestion.save()
                messages.success(request, 'Seguimiento registrado correctamente')
                return redirect('telefonica:venta_detalle', venta_id=venta.id)
        else:
            gestion_form = GestionAsesorForm()
    
    context = {
        'venta': venta,
        'gestiones_asesor': gestiones_asesor,
        'gestiones_backoffice': gestiones_backoffice,
        'gestion_form': gestion_form,
        'es_backoffice': es_backoffice(request.user),
        'titulo': f'Detalle de Venta #{venta.id}'
    }
    
    return render(request, 'telefonica/venta_detalle.html', context)

@login_required
def venta_corregir(request, venta_id):
    """Vista para corregir una venta devuelta"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Solo el asesor que creó la venta puede corregirla
    if venta.agente != request.user:
        return HttpResponseForbidden("No tienes permiso para corregir esta venta")
    
    # Solo se pueden corregir ventas devueltas
    if venta.estado_revisado != 'devuelta':
        messages.error(request, 'Esta venta no está en estado de corrección')
        return redirect('telefonica:venta_detalle', venta_id=venta.id)
    
    # Obtener la última gestión de backoffice (motivo de devolución)
    ultima_gestion = GestionBackoffice.objects.filter(
        venta=venta,
        accion='devolver'
    ).order_by('-fecha').first()
    
    if request.method == 'POST':
        form = CorreccionVentaForm(request.POST, request.FILES, instance=venta)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.estado_revisado = 'pendiente_revision'  # Vuelve a pendiente de revisión
            venta.save()
            
            # Registrar gestión del asesor
            gestion = GestionAsesor(
                venta=venta,
                asesor=request.user,
                accion='corregir',
                comentario='Venta corregida y reenviada a revisión'
            )
            gestion.save()
            
            messages.success(request, 'Venta corregida y reenviada a revisión')
            return redirect('telefonica:ventas')
    else:
        form = CorreccionVentaForm(instance=venta)
    
    context = {
        'venta': venta,
        'form': form,
        'ultima_gestion': ultima_gestion,
        'titulo': 'Corregir Venta'
    }
    
    return render(request, 'telefonica/venta_corregir.html', context)

@login_required
@user_passes_test(es_backoffice)
def venta_revisar(request, venta_id):
    """Vista para que backoffice revise una venta"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Solo se pueden revisar ventas pendientes
    if venta.estado_revisado != 'pendiente_revision':
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
            venta.estado_revisado = 'aprobada'
            mensaje = 'Venta aprobada correctamente'
        else:  # devolver
            venta.estado_revisado = 'devuelta'
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
@user_passes_test(es_backoffice)
def ventas_pendientes(request):
    """Bandeja de ventas pendientes de revisión"""
    ventas = Venta.objects.filter(estado_revisado='pendiente_revision').order_by('-fecha_creacion')
    
    paginator = Paginator(ventas, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/bandeja_pendientes.html', {
        'page_obj': page_obj,
        'titulo': 'Bandeja de Ventas Pendientes'
    })

@login_required
@user_passes_test(es_backoffice)
def bandeja_digitacion(request):
    """Bandeja de ventas aprobadas pendientes de digitación"""
    if not es_backoffice(request.user):
        messages.error(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    ventas = Venta.objects.filter(estado_revisado='aprobada').order_by('-fecha_creacion')
    
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
    # Verificar permisos
    if not es_backoffice(request.user) and not es_asesor(request.user):
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener ventas según el rol
    if es_backoffice(request.user):
        # Backoffice puede ver todas las ventas
        ventas = Venta.objects.all().order_by('-fecha_creacion')
    else:
        # Asesor solo puede ver sus ventas
        ventas = Venta.objects.filter(agente=request.user).order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(ventas, 10)  # 10 ventas por página
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
    # Verificar permisos según rol
    if es_backoffice(request.user):
        # Backoffice ve todas las ventas devueltas
        ventas = Venta.objects.filter(estado_revisado='devuelta').order_by('-fecha_creacion')
    elif es_asesor(request.user):
        # Asesor solo ve sus ventas devueltas
        ventas = Venta.objects.filter(
            agente=request.user,
            estado_revisado='devuelta'
        ).order_by('-fecha_creacion')
    else:
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Paginación
    paginator = Paginator(ventas, 10)  # 10 ventas por página
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
        ventas = Venta.objects.filter(estado_revisado__in=['digitada', 'completada']).order_by('-fecha_creacion')
    else:
        ventas = Venta.objects.filter(
            agente=request.user, 
            estado_revisado__in=['digitada', 'completada']
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
        ventas = Venta.objects.filter(estado_revisado='devuelta').order_by('-fecha_creacion')
    else:
        ventas = Venta.objects.filter(
            agente=request.user,
            estado_revisado='devuelta'
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
def buscar_cliente(request):
    """API para buscar cliente por tipo y número de documento"""
    tipo_documento = request.GET.get('tipo_documento')
    documento = request.GET.get('documento')
    
    # Validar que se proporcionen los parámetros necesarios
    if not documento:
        return JsonResponse({'found': False, 'error': 'Se requiere número de documento'})
    
    try:
        # Si se proporciona tipo_documento, buscar por ambos campos
        if tipo_documento:
            cliente = Cliente.objects.filter(
                tipo_documento=tipo_documento,
                documento=documento
            ).first()
        # Si no se proporciona tipo_documento, buscar solo por documento
        else:
            cliente = Cliente.objects.filter(documento=documento).first()
        
        if cliente:
            # Cliente encontrado, devolver sus datos
            return JsonResponse({
                'found': True,
                'tipo_documento': cliente.tipo_documento,
                'documento': cliente.documento,
                'nombres': cliente.nombres,
                'apellidos': cliente.apellidos,
                'correo': cliente.correo or '',
                'departamento': cliente.departamento,
                'ciudad': cliente.ciudad,
                'barrio': cliente.barrio or '',
                'direccion': cliente.direccion,
                'telefono': cliente.telefono
            })
        else:
            # Cliente no encontrado
            return JsonResponse({'found': False})
    except Exception as e:
        # Error en la búsqueda
        return JsonResponse({'found': False, 'error': str(e)})

@login_required
@user_passes_test(es_backoffice)
def comisiones_calcular(request):
    """Vista para calcular comisiones de ventas aprobadas"""
    if request.method == 'POST':
        ventas_ids = request.POST.getlist('ventas_ids')
        ventas = Venta.objects.filter(id__in=ventas_ids, estado_revisado='aprobada')
        
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
    ventas = Venta.objects.filter(
        estado_revisado='aprobada'
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
    if es_backoffice(request.user):
        comisiones = Comision.objects.all().order_by('-fecha_calculo')
    else:
        comisiones = Comision.objects.filter(agente=request.user).order_by('-fecha_calculo')
    
    paginator = Paginator(comisiones, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'telefonica/comisiones_lista.html', {
        'page_obj': page_obj,
        'titulo': 'Comisiones',
        'es_backoffice': es_backoffice(request.user)
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
    telefonica_groups = ['Asesores', 'Backoffice']
    
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
    if not es_backoffice(request.user):
        messages.warning(request, "No tienes permiso para acceder a esta sección")
        return redirect('telefonica:dashboard')
    
    # Obtener ventas pendientes de revisión
    ventas = Venta.objects.filter(estado_revisado='pendiente_revision').order_by('-fecha_creacion')
    
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