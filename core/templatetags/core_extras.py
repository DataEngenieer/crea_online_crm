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
        'AP': {'clase': 'bg-success text-white', 'icono': 'bi-check-circle-fill'},
        'PAGADO': {'clase': 'bg-success text-white', 'icono': 'bi-cash-coin'},
        'PAGADO - Pago formalizado': {'clase': 'bg-success text-white', 'icono': 'bi-cash-coin'},
        'SAP': {'clase': 'bg-success text-white', 'icono': 'bi-check-circle-fill'},
        'AP - Acuerdo de pago formalizado': {'clase': 'bg-success text-white', 'icono': 'bi-check-circle-fill'},
        'SALDADO_LINERU': {'clase': 'bg-success text-white', 'icono': 'bi-check-circle'},
        'Saldado con LINERU': {'clase': 'bg-success text-white', 'icono': 'bi-check-circle'},
        
        # Contacto efectivo - Negociación (azul)
        'NC': {'clase': 'bg-primary text-white', 'icono': 'bi-chat-text'},
        'SOLICITA_INFO': {'clase': 'bg-primary text-white', 'icono': 'bi-info-circle'},
        'SOLICITA_LLAMADA': {'clase': 'bg-primary text-white', 'icono': 'bi-telephone-forward'},
        'NC - Negociación en curso / pendiente de validación': {'clase': 'bg-primary text-white', 'icono': 'bi-chat-text'},
        'SOLICITA_MAS_INFORMACION': {'clase': 'bg-primary text-white', 'icono': 'bi-info-circle'},
        'SOLICITA_LLAMADA_POSTERIOR': {'clase': 'bg-primary text-white', 'icono': 'bi-telephone-forward'},
        'SIN_RESPUESTA_WP': {'clase': 'bg-primary text-white', 'icono': 'bi-whatsapp'},
        'Sin respuesta en WhatsApp': {'clase': 'bg-primary text-white', 'icono': 'bi-whatsapp'},
        
        # Contacto efectivo - Problemas (naranja/ámbar)
        'RN': {'clase': 'bg-warning text-dark', 'icono': 'bi-x-circle'},
        'ND': {'clase': 'bg-warning text-dark', 'icono': 'bi-question-circle'},
        'ABOGADO': {'clase': 'bg-warning text-dark', 'icono': 'bi-briefcase'},
        'NO_CAPACIDAD_PAGO': {'clase': 'bg-warning text-dark', 'icono': 'bi-wallet'},
        'RECLAMO': {'clase': 'bg-warning text-dark', 'icono': 'bi-exclamation-triangle'},
        'RN - Rechaza negociación': {'clase': 'bg-warning text-dark', 'icono': 'bi-x-circle'},
        'ND - Niega deuda': {'clase': 'bg-warning text-dark', 'icono': 'bi-question-circle'},
        'REMITE_ABOGADO': {'clase': 'bg-warning text-dark', 'icono': 'bi-briefcase'},
        'TRAMITE_RECLAMO': {'clase': 'bg-warning text-dark', 'icono': 'bi-exclamation-triangle'},
        
        # Contacto no efectivo (gris azulado)
        'TELEFONO_APAGADO': {'clase': 'bg-info text-white', 'icono': 'bi-phone-vibrate'},
        'NO_CONTESTA': {'clase': 'bg-info text-white', 'icono': 'bi-telephone-x'},
        'BUZON_VOZ': {'clase': 'bg-info text-white', 'icono': 'bi-voicemail'},
        'Teléfono apagado / fuera de servicio': {'clase': 'bg-info text-white', 'icono': 'bi-phone-vibrate'},
        'NO_CONTESTA': {'clase': 'bg-info text-white', 'icono': 'bi-telephone-x'},
        'No contesta': {'clase': 'bg-info text-white', 'icono': 'bi-telephone-x'},
        'BUZON_VOZ': {'clase': 'bg-info text-white', 'icono': 'bi-voicemail'},
        'Buzón de voz': {'clase': 'bg-info text-white', 'icono': 'bi-voicemail'},
        'SIN_RESPUESTA_WP': {'clase': 'bg-info text-white', 'icono': 'bi-whatsapp'},
        
        
        # Contacto fallido (rojo)
        'NUMERO_EQUIVOCADO': {'clase': 'bg-danger text-white', 'icono': 'bi-x-octagon'},
        'NUMERO_INEXISTENTE': {'clase': 'bg-danger text-white', 'icono': 'bi-slash-circle'},
        'Número equivocado': {'clase': 'bg-danger text-white', 'icono': 'bi-x-octagon'},
        'Número inexistente': {'clase': 'bg-danger text-white', 'icono': 'bi-slash-circle'},
        
        # Terceros (morado)
        'TERCERO_INFORMACION': {'clase': 'bg-purple text-white', 'icono': 'bi-people'},
        'TERCERO_NO_INFORMACION': {'clase': 'bg-purple text-white', 'icono': 'bi-people-slash'},
        'Tercero brinda información': {'clase': 'bg-purple text-white', 'icono': 'bi-people'},
        'Tercero no brinda información': {'clase': 'bg-purple text-white', 'icono': 'bi-people-slash'},
        
        # Sin gestiones (gris)
        'Sin gestiones': {'clase': 'bg-secondary text-white', 'icono': 'bi-dash-circle'},
        'Sin tipificación': {'clase': 'bg-secondary text-white', 'icono': 'bi-question-diamond'},
        '': {'clase': 'bg-light text-dark', 'icono': 'bi-question-diamond'},  # Estado vacío
    }
    
    # Valor por defecto si no se encuentra la tipificación
    default = {'clase': 'bg-secondary', 'icono': 'bi-question-diamond'}
    
    return estilos.get(tipificacion, default)