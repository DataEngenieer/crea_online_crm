from django import template

register = template.Library()

def map_estado_color(estado):
    """
    Devuelve el color de Bootstrap según el estado de la auditoría.
    """
    colores = {
        'pendiente': 'secondary',
        'en_progreso': 'info',
        'completada': 'success',
        'revision': 'warning',
        'rechazada': 'danger',
    }
    return colores.get(str(estado).lower(), 'secondary')

def map_estado_icon(estado):
    """
    Devuelve el ícono de Font Awesome según el estado de la auditoría.
    """
    iconos = {
        'pendiente': 'clock',
        'en_progreso': 'spinner',
        'completada': 'check-circle',
        'revision': 'search',
        'rechazada': 'times-circle',
    }
    return iconos.get(str(estado).lower(), 'question-circle')

# Registrar los filtros
register.filter('map_estado_color', map_estado_color)
register.filter('map_estado_icon', map_estado_icon)

@register.filter
def get_estado_badge(value):
    """
    Devuelve HTML para un badge de estado según el valor recibido.
    Ejemplo de valores: 'aprobado', 'rechazado', 'pendiente', etc.
    """
    colores = {
        'aprobado': 'success',
        'rechazado': 'danger',
        'pendiente': 'warning',
        'en_proceso': 'info',
        '': 'secondary',
        None: 'secondary',
    }
    color = colores.get(str(value).lower(), 'secondary')
    texto = str(value).capitalize() if value else 'Sin estado'
    return f'<span class="badge bg-{color}">{texto}</span>'

get_estado_badge.is_safe = True

@register.filter
def get_puntaje_color(value):
    """
    Devuelve la clase de color de Bootstrap según el puntaje numérico.
    - >= 90: 'success'
    - >= 70: 'info'
    - >= 50: 'warning'
    - < 50: 'danger'
    """
    try:
        puntaje = float(value)
    except (TypeError, ValueError):
        return 'secondary'
    if puntaje >= 90:
        return 'success'
    elif puntaje >= 70:
        return 'info'
    elif puntaje >= 50:
        return 'warning'
    else:
        return 'danger'

@register.filter
def get_puntaje_simple_color(value):
    """
    Devuelve la clase de color Bootstrap según el puntaje, igual que get_puntaje_color.
    """
    try:
        puntaje = float(value)
    except (TypeError, ValueError):
        return 'secondary'
    if puntaje >= 90:
        return 'success'
    elif puntaje >= 70:
        return 'info'
    elif puntaje >= 50:
        return 'warning'
    else:
        return 'danger'

@register.filter
def get_puntaje_text_color(value):
    """
    Devuelve la clase de color de texto de Bootstrap según el puntaje numérico.
    - >= 90: 'text-success' (verde)
    - >= 70: 'text-info' (azul claro)
    - >= 50: 'text-warning' (amarillo/naranja)
    - < 50: 'text-danger' (rojo)
    """
    try:
        puntaje = float(value)
    except (TypeError, ValueError):
        return 'text-secondary'
    
    if puntaje >= 90:
        return 'text-success'
    elif puntaje >= 70:
        return 'text-info'
    elif puntaje >= 50:
        return 'text-warning'
    else:
        return 'text-danger'

@register.filter
def map(iterable, attr):
    """
    Filtro personalizado para mapear una lista de objetos a una lista de atributos.
    Uso: {{ lista_objetos|map:'atributo' }} o {{ lista_objetos|map(attribute='atributo') }}
    """
    if not iterable:
        return []
        
    # Si el atributo viene como 'attribute=valor' (sintaxis de Jinja2)
    if isinstance(attr, str) and attr.startswith('attribute='):
        attr = attr.split('=')[1].strip('"\'')
    
    return [getattr(item, attr, None) for item in iterable]

@register.filter
def map_tipo_monitoreo_color(tipo_monitoreo):
    """
    Devuelve el color de Bootstrap según el tipo de monitoreo.
    """
    colores = {
        'speech': 'primary',
        'al_lado': 'success',
        'grabacion': 'info',
        'remoto': 'warning',
    }
    return colores.get(str(tipo_monitoreo).lower(), 'secondary')

@register.filter(name='tojson')
def to_json(value):
    """
    Convierte un valor a formato JSON seguro para usar en JavaScript.
    Uso: {{ valor|tojson|safe }}
    """
    import json
    from django.utils.safestring import mark_safe
    return mark_safe(json.dumps(value, ensure_ascii=False))

@register.filter
def replace(value, args):
    """
    Reemplaza todas las ocurrencias de una cadena por otra.
    Uso: {{ texto|replace:"buscar,reemplazar" }}
    """
    if not value or not args:
        return value
    
    try:
        search, replace_with = args.split(',', 1)
        return str(value).replace(search, replace_with)
    except ValueError:
        return value