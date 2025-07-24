# calidad/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages

class RestrictIPMiddleware:
    """
    Middleware para restringir el acceso a la aplicación de calidad por IP.
    Los superusuarios y administradores tienen acceso sin restricciones.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Solo aplicar a rutas de la aplicación de calidad
        if request.path.startswith('/calidad/'):
            # Permitir acceso a superusuarios y administradores sin verificación de IP
            if hasattr(request, 'user') and request.user.is_authenticated:
                if request.user.is_superuser or request.user.groups.filter(name='Administrador').exists():
                    return self.get_response(request)
            
            ips_permitidas = getattr(settings, 'IPS_PERMITIDAS', [])
            
            # Si no hay IPs permitidas configuradas, permitir el acceso
            if not ips_permitidas:
                return self.get_response(request)
                
            # Obtener la IP real del cliente (considerando proxies)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_cliente = x_forwarded_for.split(',')[0].strip()
            else:
                ip_cliente = request.META.get('REMOTE_ADDR')
            
            # Si la IP del cliente no está en la lista de permitidas
            if ip_cliente not in ips_permitidas:
                # Si es una petición AJAX, devolver error 403
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse(
                        {'error': 'Acceso restringido. IP no autorizada.'}, 
                        status=403
                    )
                
                # Si es una petición normal, redirigir al login con mensaje de error
                from django.contrib import messages
                from django.contrib.auth.views import redirect_to_login
                
                # Usar la vista de login personalizada si está disponible
                login_url = reverse('login')
                
                # Redirigir al login con mensaje de error
                response = redirect(f"{login_url}?next={request.path}")
                
                # Configurar mensaje para la próxima solicitud
                from django.contrib.messages import get_messages
                storage = get_messages(request)
                
                # Limpiar mensajes existentes para evitar duplicados
                for _ in storage._loaded_messages:
                    pass
                    
                # Agregar mensaje de error
                storage.add(
                    messages.ERROR,
                    f"Acceso restringido. Su IP ({ip_cliente}) no está autorizada para acceder al portal de Calidad. "
                    "Por favor, contacte al administrador si cree que esto es un error.",
                    extra_tags='ip_restricted'
                )
                
                return response
        
        return self.get_response(request)