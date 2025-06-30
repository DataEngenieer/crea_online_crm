from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.template import RequestContext

class TelefonicaMenuMiddleware(MiddlewareMixin):
    """
    Middleware para agregar el menú lateral de Telefónica al contexto de todas las respuestas.
    Esto permite que el menú se muestre en todas las páginas sin modificar la plantilla base.
    """
    
    def process_template_response(self, request, response):
        if hasattr(response, 'context_data') and isinstance(response.context_data, dict):
            # Solo procesamos respuestas que tienen contexto y es un diccionario
            response.context_data['telefonica_menu_enabled'] = True
        return response