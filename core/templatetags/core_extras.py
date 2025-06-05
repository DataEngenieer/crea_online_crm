from django import template
from datetime import datetime
from ..utils import determinar_estado_cliente
import locale

register = template.Library()

@register.filter
def formato_numero(valor):
    """Formatea un número con separación de miles usando punto y dos decimales
    
    Args:
        valor: Número a formatear
        
    Returns:
        str: Número formateado con separación de miles y dos decimales
    """
    try:
        # Convertir a float si es necesario
        if valor is None:
            return '0,00'
        
        valor_float = float(valor)
        # Formatear con separador de miles y dos decimales
        # Usamos el formato español: punto como separador de miles y coma para decimales
        return '{:,.2f}'.format(valor_float).replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return '0,00'

@register.filter
def get_item(lista_o_dict, key):
    """Obtiene un valor de un diccionario o lista por su clave o índice
    
    Args:
        lista_o_dict: Diccionario o lista
        key: Clave o índice
        
    Returns:
        El valor correspondiente a la clave o índice
    """
    try:
        if isinstance(lista_o_dict, dict):
            return lista_o_dict.get(key)
        elif isinstance(lista_o_dict, (list, tuple)) and isinstance(key, int) and 0 <= key < len(lista_o_dict):
            return lista_o_dict[key]
        return None
    except (IndexError, TypeError):
        return None
        
@register.filter
def get_range(value):
    """Genera un rango de números desde 0 hasta value-1
    
    Args:
        value: Número entero o longitud de una lista
        
    Returns:
        range: Rango de números desde 0 hasta value-1
    """
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def estado_cliente(cliente, gestiones=None):
    """Determina el estado de un cliente utilizando la función utilitaria
    
    Args:
        cliente: Objeto cliente o diccionario con datos del cliente
        gestiones: Lista o queryset de gestiones del cliente
        
    Returns:
        dict: Diccionario con información del estado
    """
    return determinar_estado_cliente(cliente, gestiones)

@register.filter
def estilo_tipificacion(tipificacion):
    """Devuelve el estilo (color e icono) para una tipificación de gestión
    
    Args:
        tipificacion: Código o nombre de la tipificación
        
    Returns:
        dict: Diccionario con clase CSS e icono
    """
    # Mapeo de tipificaciones a estilos
    estilos = {
        # Contacto efectivo - Acuerdos y pagos (verde)
        'ap': {'clase': 'bg-success', 'icono': 'bi-check-circle-fill'},
        'pp': {'clase': 'bg-success', 'icono': 'bi-calendar-check'},
        'pagado': {'clase': 'bg-success', 'icono': 'bi-cash-coin'},
        'AP - Acuerdo de pago formalizado': {'clase': 'bg-success', 'icono': 'bi-check-circle-fill'},
        'PP - Promesa de pago': {'clase': 'bg-success', 'icono': 'bi-calendar-check'},
        'PAGADO': {'clase': 'bg-success', 'icono': 'bi-cash-coin'},
        
        # Contacto efectivo - Negociación (azul)
        'nc': {'clase': 'bg-primary', 'icono': 'bi-chat-text'},
        'solicita_info': {'clase': 'bg-primary', 'icono': 'bi-info-circle'},
        'solicita_llamada': {'clase': 'bg-primary', 'icono': 'bi-telephone-forward'},
        'NC - Negociación en curso / pendiente de validación': {'clase': 'bg-primary', 'icono': 'bi-chat-text'},
        'Solicita más información': {'clase': 'bg-primary', 'icono': 'bi-info-circle'},
        'Solicita llamada posterior': {'clase': 'bg-primary', 'icono': 'bi-telephone-forward'},
        
        # Contacto efectivo - Problemas (naranja)
        'rn': {'clase': 'bg-warning text-dark', 'icono': 'bi-x-circle'},
        'nd': {'clase': 'bg-warning text-dark', 'icono': 'bi-question-circle'},
        'abogado': {'clase': 'bg-warning text-dark', 'icono': 'bi-briefcase'},
        'no_capacidad': {'clase': 'bg-warning text-dark', 'icono': 'bi-wallet'},
        'reclamo': {'clase': 'bg-warning text-dark', 'icono': 'bi-exclamation-triangle'},
        'RN - Rechaza negociación': {'clase': 'bg-warning text-dark', 'icono': 'bi-x-circle'},
        'ND - Niega deuda': {'clase': 'bg-warning text-dark', 'icono': 'bi-question-circle'},
        'Remite a abogado': {'clase': 'bg-warning text-dark', 'icono': 'bi-briefcase'},
        'No tiene capacidad de pago': {'clase': 'bg-warning text-dark', 'icono': 'bi-wallet'},
        'Trámite de reclamo en curso': {'clase': 'bg-warning text-dark', 'icono': 'bi-exclamation-triangle'},
        
        # Contacto no efectivo (gris azulado)
        'telefono_apagado': {'clase': 'bg-info text-dark', 'icono': 'bi-phone-vibrate'},
        'no_contesta': {'clase': 'bg-info text-dark', 'icono': 'bi-telephone-x'},
        'buzon_voz': {'clase': 'bg-info text-dark', 'icono': 'bi-voicemail'},
        'Teléfono apagado / fuera de servicio': {'clase': 'bg-info text-dark', 'icono': 'bi-phone-vibrate'},
        'No contesta': {'clase': 'bg-info text-dark', 'icono': 'bi-telephone-x'},
        'Buzón de voz': {'clase': 'bg-info text-dark', 'icono': 'bi-voicemail'},
        
        # Contacto fallido (rojo)
        'numero_equivocado': {'clase': 'bg-danger', 'icono': 'bi-x-octagon'},
        'numero_inexistente': {'clase': 'bg-danger', 'icono': 'bi-slash-circle'},
        'Número equivocado': {'clase': 'bg-danger', 'icono': 'bi-x-octagon'},
        'Número inexistente': {'clase': 'bg-danger', 'icono': 'bi-slash-circle'},
        
        # Terceros (morado)
        'tercero_informacion': {'clase': 'bg-purple', 'icono': 'bi-people'},
        'tercero_no_informacion': {'clase': 'bg-purple', 'icono': 'bi-people-slash'},
        'Tercero brinda información': {'clase': 'bg-purple', 'icono': 'bi-people'},
        'Tercero no brinda información': {'clase': 'bg-purple', 'icono': 'bi-people-slash'},
        
        # Sin gestiones (gris)
        'Sin gestiones': {'clase': 'bg-secondary', 'icono': 'bi-dash-circle'},
        'Sin tipificación': {'clase': 'bg-secondary', 'icono': 'bi-question-diamond'},
    }
    
    # Valor por defecto si no se encuentra la tipificación
    default = {'clase': 'bg-secondary', 'icono': 'bi-question-diamond'}
    
    return estilos.get(tipificacion, default)