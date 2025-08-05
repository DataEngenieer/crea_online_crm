# core/views_ip_management.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
import requests
import json
from .models import IPPermitida, RegistroAccesoIP
from django.conf import settings


def es_admin(user):
    """
    Verifica si el usuario es administrador o superusuario.
    """
    return user.is_superuser or user.groups.filter(name='Administrador').exists()


@login_required
@user_passes_test(es_admin)
def gestionar_ips_permitidas(request):
    """
    Vista para gestionar las IPs permitidas en el sistema.
    """
    # Obtener todas las IPs permitidas
    ips_permitidas = IPPermitida.objects.all().order_by('-fecha_creacion')
    
    # Filtros de búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        ips_permitidas = ips_permitidas.filter(
            Q(ip_address__icontains=search_query) |
            Q(descripcion__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(ips_permitidas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_ips': IPPermitida.objects.count(),
        'ips_activas': IPPermitida.objects.filter(activa=True).count(),
    }
    
    return render(request, 'core/gestionar_ips_permitidas.html', context)


@login_required
@user_passes_test(es_admin)
def agregar_ip_permitida(request):
    """
    Vista para agregar una nueva IP permitida.
    """
    if request.method == 'POST':
        ip_address = request.POST.get('ip_address', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        
        if not ip_address or not descripcion:
            messages.error(request, 'La dirección IP y la descripción son obligatorias.')
            return redirect('core:gestionar_ips_permitidas')
        
        # Verificar si la IP ya existe
        if IPPermitida.objects.filter(ip_address=ip_address).exists():
            messages.error(request, f'La IP {ip_address} ya está registrada en el sistema.')
            return redirect('core:gestionar_ips_permitidas')
        
        try:
            # Crear la nueva IP permitida
            ip_permitida = IPPermitida.objects.create(
                ip_address=ip_address,
                descripcion=descripcion,
                usuario_creacion=request.user
            )
            
            messages.success(request, f'IP {ip_address} agregada exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al agregar la IP: {str(e)}')
    
    return redirect('core:gestionar_ips_permitidas')


@login_required
@user_passes_test(es_admin)
@require_POST
def toggle_ip_status(request, ip_id):
    """
    Vista para activar/desactivar una IP permitida.
    """
    try:
        ip_permitida = get_object_or_404(IPPermitida, id=ip_id)
        ip_permitida.activa = not ip_permitida.activa
        ip_permitida.save()
        
        estado = 'activada' if ip_permitida.activa else 'desactivada'
        messages.success(request, f'IP {ip_permitida.ip_address} {estado} exitosamente.')
        
    except Exception as e:
        messages.error(request, f'Error al cambiar el estado de la IP: {str(e)}')
    
    return redirect('core:gestionar_ips_permitidas')


@login_required
@user_passes_test(es_admin)
@require_POST
def eliminar_ip_permitida(request, ip_id):
    """
    Vista para eliminar una IP permitida.
    """
    try:
        ip_permitida = get_object_or_404(IPPermitida, id=ip_id)
        ip_address = ip_permitida.ip_address
        ip_permitida.delete()
        
        messages.success(request, f'IP {ip_address} eliminada exitosamente.')
        
    except Exception as e:
        messages.error(request, f'Error al eliminar la IP: {str(e)}')
    
    return redirect('core:gestionar_ips_permitidas')


@login_required
@user_passes_test(es_admin)
def registros_acceso_ip(request):
    """
    Vista para ver los registros de acceso por IP.
    """
    # Obtener todos los registros de acceso
    registros = RegistroAccesoIP.objects.all().order_by('-fecha_acceso')
    
    # Filtros
    tipo_acceso = request.GET.get('tipo_acceso', '')
    search_query = request.GET.get('search', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if tipo_acceso:
        registros = registros.filter(tipo_acceso=tipo_acceso)
    
    if search_query:
        registros = registros.filter(
            Q(ip_address__icontains=search_query) |
            Q(usuario__username__icontains=search_query) |
            Q(pais__icontains=search_query) |
            Q(ciudad__icontains=search_query) |
            Q(isp__icontains=search_query)
        )
    
    if fecha_desde:
        registros = registros.filter(fecha_acceso__date__gte=fecha_desde)
    
    if fecha_hasta:
        registros = registros.filter(fecha_acceso__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_registros = RegistroAccesoIP.objects.count()
    logins_exitosos = RegistroAccesoIP.objects.filter(tipo_acceso='login_exitoso').count()
    logins_fallidos = RegistroAccesoIP.objects.filter(tipo_acceso='login_fallido').count()
    ips_bloqueadas = RegistroAccesoIP.objects.filter(tipo_acceso='ip_bloqueada').count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'tipo_acceso': tipo_acceso,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_registros': total_registros,
        'logins_exitosos': logins_exitosos,
        'logins_fallidos': logins_fallidos,
        'ips_bloqueadas': ips_bloqueadas,
        'tipos_acceso': RegistroAccesoIP.TIPO_ACCESO_CHOICES,
    }
    
    return render(request, 'core/registros_acceso_ip.html', context)


@login_required
@user_passes_test(es_admin)
def consultar_ip_info(request):
    """
    Vista AJAX para consultar información de una IP usando la API de ipquery.io.
    """
    if request.method == 'GET':
        ip_address = request.GET.get('ip', '').strip()
        
        if not ip_address:
            return JsonResponse({'error': 'IP address is required'}, status=400)
        
        try:
            # Consultar la API de ipquery.io
            response = requests.get(f'https://api.ipquery.io/{ip_address}', timeout=10)
            
            if response.status_code == 200:
                ip_info = response.json()
                
                # Formatear la respuesta para el frontend
                formatted_info = {
                    'ip': ip_info.get('ip'),
                    'pais': ip_info.get('location', {}).get('country'),
                    'ciudad': ip_info.get('location', {}).get('city'),
                    'region': ip_info.get('location', {}).get('state'),
                    'codigo_postal': ip_info.get('location', {}).get('zipcode'),
                    'latitud': ip_info.get('location', {}).get('latitude'),
                    'longitud': ip_info.get('location', {}).get('longitude'),
                    'zona_horaria': ip_info.get('location', {}).get('timezone'),
                    'isp': ip_info.get('isp', {}).get('isp'),
                    'organizacion': ip_info.get('isp', {}).get('org'),
                    'asn': ip_info.get('isp', {}).get('asn'),
                    'es_movil': ip_info.get('risk', {}).get('is_mobile', False),
                    'es_vpn': ip_info.get('risk', {}).get('is_vpn', False),
                    'es_tor': ip_info.get('risk', {}).get('is_tor', False),
                    'es_proxy': ip_info.get('risk', {}).get('is_proxy', False),
                    'es_datacenter': ip_info.get('risk', {}).get('is_datacenter', False),
                    'puntuacion_riesgo': ip_info.get('risk', {}).get('risk_score', 0),
                }
                
                return JsonResponse({
                    'success': True,
                    'data': formatted_info
                })
            else:
                return JsonResponse({
                    'error': f'Error al consultar la API: {response.status_code}'
                }, status=response.status_code)
                
        except requests.RequestException as e:
            return JsonResponse({
                'error': f'Error de conexión: {str(e)}'
            }, status=500)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'error': f'Error al procesar la respuesta: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@user_passes_test(es_admin)
def obtener_mi_ip(request):
    """
    Vista AJAX para obtener la IP actual del usuario.
    """
    # Obtener la IP real del cliente
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Verificar si es una IP de Cloudflare
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        ip = cf_connecting_ip
    
    return JsonResponse({
        'success': True,
        'ip': ip
    })