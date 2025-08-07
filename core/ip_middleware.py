# core/ip_middleware.py
import requests
import json
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import IPPermitida, RegistroAccesoIP
import logging

logger = logging.getLogger(__name__)

class IPRestrictionMiddleware(MiddlewareMixin):
    """
    Middleware para restringir el acceso al CRM por IP en producción.
    Integra con la API de ipquery.io para obtener información detallada de la IP.
    """
    
    # URLs que están exentas de la verificación de IP
    EXEMPT_URLS = [
        '/admin/',  # Panel de administración de Django
        '/static/',  # Archivos estáticos
        '/media/',   # Archivos de media
        '/login/',   # Página de login para evitar bucles infinitos
        '/logout/',  # Página de logout
        '/password_reset/',  # Páginas de recuperación de contraseña
        '/reset/',   # Páginas de confirmación de reset
        '/favicon.ico',  # Favicon
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Verificar si el sistema de restricción de IP está habilitado
        ip_restriction_enabled = getattr(settings, 'IP_RESTRICTION_ENABLED', False)
        
        # Logging de depuración para entender por qué se ejecuta el middleware
        logger.debug(f"IP Middleware Debug - ip_restriction_enabled: {ip_restriction_enabled}, DEBUG: {settings.DEBUG}")
        
        # Solo aplicar restricciones si está habilitado y en producción
        if ip_restriction_enabled and not settings.DEBUG:
            # Verificar si la URL está exenta
            if not self._is_exempt_url(request.path):
                # Obtener la IP real del cliente
                ip_cliente = self._get_client_ip(request)
                
                # Verificar si la IP está permitida
                if IPPermitida.ip_esta_permitida(ip_cliente):
                    # IP permitida - permitir acceso a cualquier usuario autenticado
                    # Registrar acceso exitoso y actualizar último acceso
                    IPPermitida.registrar_acceso(ip_cliente)
                    
                    # Determinar tipo de acceso según el usuario
                    tipo_acceso = 'acceso_privilegiado' if self._is_privileged_user(request) else 'acceso_permitido'
                    self._registrar_acceso(request, ip_cliente, tipo_acceso)
                else:
                    # IP no permitida - verificar si el usuario es privilegiado (bypass para emergencias)
                    if self._is_privileged_user(request):
                        # Registrar acceso de usuario privilegiado con IP no permitida
                        self._registrar_acceso(request, ip_cliente, 'acceso_privilegiado_bypass')
                        return self.get_response(request)
                    
                    # Obtener información detallada de la IP
                    ip_info = self._get_ip_info(ip_cliente)
                    
                    # Registrar intento de acceso bloqueado
                    self._registrar_acceso_detallado(request, ip_cliente, 'ip_bloqueada', ip_info)
                    
                    # Bloquear acceso
                    return self._block_access(request, ip_cliente, ip_info)
        
        return self.get_response(request)
    
    def _is_exempt_url(self, path):
        """
        Verifica si la URL está exenta de la verificación de IP.
        """
        return any(path.startswith(exempt_url) for exempt_url in self.EXEMPT_URLS)
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP real del cliente considerando proxies y load balancers.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Tomar la primera IP de la lista (IP original del cliente)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Verificar si es una IP de Cloudflare o proxy conocido
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            ip = cf_connecting_ip
            
        return ip
    
    def _is_privileged_user(self, request):
        """
        Verifica si el usuario es superusuario o administrador.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return (request.user.is_superuser or 
                   request.user.groups.filter(name='Administrador').exists())
        return False
    
    def _get_ip_info(self, ip_address):
        """
        Obtiene información detallada de la IP usando la API de ipquery.io.
        """
        try:
            # Hacer petición a la API de ipquery.io
            response = requests.get(f'https://api.ipquery.io/{ip_address}', timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Error al consultar IP {ip_address}: Status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error de conexión al consultar IP {ip_address}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar respuesta JSON para IP {ip_address}: {str(e)}")
            return None
    
    def _registrar_acceso(self, request, ip_address, tipo_acceso):
        """
        Registra un acceso básico sin información detallada de IP.
        """
        try:
            RegistroAccesoIP.objects.create(
                usuario=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                ip_address=ip_address,
                tipo_acceso=tipo_acceso,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar longitud
            )
        except Exception as e:
            logger.error(f"Error al registrar acceso: {str(e)}")
    
    def _registrar_acceso_detallado(self, request, ip_address, tipo_acceso, ip_info):
        """
        Registra un acceso con información detallada de la IP.
        """
        try:
            # Extraer información de la respuesta de ipquery.io
            pais = None
            ciudad = None
            isp = None
            es_vpn = False
            es_proxy = False
            puntuacion_riesgo = 0
            
            if ip_info:
                location = ip_info.get('location', {})
                isp_info = ip_info.get('isp', {})
                risk_info = ip_info.get('risk', {})
                
                pais = location.get('country')
                ciudad = location.get('city')
                isp = isp_info.get('isp')
                es_vpn = risk_info.get('is_vpn', False)
                es_proxy = risk_info.get('is_proxy', False)
                puntuacion_riesgo = risk_info.get('risk_score', 0)
            
            RegistroAccesoIP.objects.create(
                usuario=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                ip_address=ip_address,
                tipo_acceso=tipo_acceso,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                pais=pais,
                ciudad=ciudad,
                isp=isp,
                es_vpn=es_vpn,
                es_proxy=es_proxy,
                puntuacion_riesgo=puntuacion_riesgo
            )
        except Exception as e:
            logger.error(f"Error al registrar acceso detallado: {str(e)}")
    
    def _block_access(self, request, ip_address, ip_info):
        """
        Bloquea el acceso y retorna la respuesta apropiada.
        """
        # Crear mensaje de error con información de la IP
        mensaje_base = f"Acceso restringido. Su IP ({ip_address}) no está autorizada para acceder al CRM."
        
        # Agregar información adicional si está disponible
        if ip_info:
            location = ip_info.get('location', {})
            if location.get('city') and location.get('country'):
                mensaje_base += f" Ubicación detectada: {location.get('city')}, {location.get('country')}."
        
        mensaje_base += " Por favor, contacte al administrador si cree que esto es un error."
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Acceso restringido. IP no autorizada.',
                'ip': ip_address,
                'mensaje': mensaje_base
            }, status=403)
        
        # Para peticiones normales, devolver una respuesta HTTP 403 directa
        # en lugar de redirigir al login para evitar bucles infinitos
        from django.http import HttpResponseForbidden
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Acceso Restringido - CRM</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 4rem;
                    color: #dc3545;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    color: #dc3545;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #6c757d;
                    line-height: 1.6;
                    margin-bottom: 1rem;
                }}
                .ip-info {{
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 4px;
                    margin: 1rem 0;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">🚫</div>
                <h1>Acceso Restringido</h1>
                <p>{mensaje_base}</p>
                <div class="ip-info">
                    IP detectada: {ip_address}
                </div>
                <p><strong>Si cree que esto es un error, contacte al administrador del sistema.</strong></p>
            </div>
        </body>
        </html>
        """
        
        return HttpResponseForbidden(html_content)