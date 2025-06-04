from django import template
from datetime import datetime
from ..utils import determinar_estado_cliente

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario por su clave"""
    return dictionary.get(key)

@register.filter
def estado_cliente(cliente, gestiones=None):
    """Determina el estado de un cliente utilizando la función utilitaria
    
    Args:
        cliente: Objeto cliente o diccionario con datos del cliente
        gestiones: Lista o queryset de gestiones del cliente
        
    Returns:
        dict: Diccionario con información del estado
    """
    today = datetime.now().date()
    # Tratar de obtener el cliente real si solo tenemos un diccionario
    from ..models import Cliente
    if isinstance(cliente, dict) and 'documento' in cliente:
        try:
            # Intentamos obtener el objeto Cliente real
            cliente_obj = Cliente.objects.filter(documento=cliente['documento']).first()
            if cliente_obj:
                cliente = cliente_obj
        except Exception as e:
            # Si hay algún error, continuamos con el diccionario
            print(f"Error al obtener cliente: {e}")
    
    return determinar_estado_cliente(cliente, gestiones, today)