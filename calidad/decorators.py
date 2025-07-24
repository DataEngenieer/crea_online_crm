from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.core.exceptions import PermissionDenied

def grupo_requerido(*nombres_grupos):
    """
    Decorador para verificar que el usuario pertenece a uno de los grupos especificados.
    Si tiene permiso, lo deja pasar a la vista, de lo contrario redirige según el grupo.
    """
    def decorador(vista):
        @wraps(vista)
        def _vista_envuelta(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
                
            # Verificar si el usuario es superusuario o está en alguno de los grupos (case-insensitive)
            grupos_usuario = [grupo.name.lower() for grupo in request.user.groups.all()]
            grupos_requeridos = [grupo.lower() for grupo in nombres_grupos]
            
            if request.user.is_superuser or any(grupo in grupos_usuario for grupo in grupos_requeridos):
                return vista(request, *args, **kwargs)
                
            # Si no tiene permiso, redirigir según el grupo
            if request.user.groups.filter(name='Colaborador').exists():
                return redirect('inicio')
            elif request.user.groups.filter(name='Calidad').exists():
                return redirect('calidad:dashboard')
            else:
                raise PermissionDenied("No tiene permiso para acceder a esta sección.")
        return _vista_envuelta
    return decorador

def ip_permitida(vista):
    """
    Decorador para verificar si la IP del usuario está permitida para acceder a la vista.
    Los superusuarios y administradores tienen acceso sin restricciones de IP.
    """
    @wraps(vista)
    def _vista_envuelta(request, *args, **kwargs):
        # Si no es una ruta de calidad, permitir el acceso
        if not request.path.startswith('/calidad/'):
            return vista(request, *args, **kwargs)
        
        # Permitir acceso a superusuarios y administradores sin verificación de IP (case-insensitive)
        if request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name__iexact='Administrador').exists()):
            return vista(request, *args, **kwargs)
            
        # Obtener la IP del cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_cliente = x_forwarded_for.split(',')[0].strip()
        else:
            ip_cliente = request.META.get('REMOTE_ADDR')
        
        # Obtener IPs permitidas desde settings
        from django.conf import settings
        from django.contrib import messages
        ips_permitidas = getattr(settings, 'IPS_PERMITIDAS', [])
        
        # Si hay IPs permitidas y la IP del cliente no está en la lista
        if ips_permitidas and ip_cliente not in ips_permitidas:
            from django.contrib import messages
            from django.shortcuts import redirect
            from django.urls import reverse
            
            # Guardar mensaje de error
            messages.error(
                request,
                f"Acceso restringido. Su IP ({ip_cliente}) no está autorizada para acceder al portal de Calidad. "
                "Por favor, contacte al administrador si cree que esto es un error.",
                extra_tags='ip_restricted'
            )
            
            # Redirigir al login con un parámetro para mostrar el mensaje
            return redirect(f"{reverse('login')}?next={request.path}")
            
        return vista(request, *args, **kwargs)
    return _vista_envuelta
