from django import template

register = template.Library()

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
