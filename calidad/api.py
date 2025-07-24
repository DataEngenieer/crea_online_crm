import logging
import json
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .decorators import grupo_requerido, ip_permitida

# Configurar logger
logger = logging.getLogger(__name__)

# Decorador personalizado para la API
def api_auth_required(view_func):
    """
    Decorador que combina autenticación, grupo requerido y validación de IP
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Se requiere autenticación'}, 
                status=401
            )
            
        # Verificar si el usuario es superusuario o está en los grupos permitidos
        if not (request.user.is_superuser or 
               request.user.groups.filter(name__in=['Calidad', 'Administrador']).exists()):
            return JsonResponse(
                {'error': 'No tiene permiso para realizar esta acción'}, 
                status=403
            )
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@require_http_methods(["GET"])
@csrf_exempt  # Temporalmente deshabilitar CSRF para pruebas
@api_auth_required
def buscar_usuarios(request):
    """
    Vista de API para buscar usuarios por nombre, apellido o username.
    Requiere autenticación y permisos de Calidad o Administrador.
    """
    try:
        # Registrar la solicitud recibida
        logger.debug(f"Solicitud de búsqueda recibida: {request.GET}")
        
        query = request.GET.get('q', '').strip()
        
        if not query:
            logger.debug("Búsqueda vacía, retornando resultados vacíos")
            return JsonResponse({'results': []})
        
        logger.debug(f"Buscando usuarios con término: {query}")
        
        User = get_user_model()
        
        # Buscar usuarios que coincidan con la consulta en nombre, apellido o username
        usuarios = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).order_by('first_name', 'last_name')
        
        logger.debug(f"Se encontraron {usuarios.count()} usuarios")
        
        # Formatear resultados para Select2
        results = [{
            'id': user.id,
            'text': f"{user.get_full_name()} ({user.username})",
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        } for user in usuarios]
        
        response_data = {
            'results': results,
            'pagination': {
                'more': False  # Deshabilitar paginación por ahora
            }
        }
        
        logger.debug(f"Respuesta generada: {response_data}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error en la búsqueda de usuarios: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'Ocurrió un error al buscar usuarios'}, 
            status=500
        )
