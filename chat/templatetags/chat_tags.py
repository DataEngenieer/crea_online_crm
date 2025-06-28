from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def es_supervisor(user):
    """Devuelve True si el usuario es superusuario o pertenece al grupo supervisor."""
    return user.is_superuser or user.groups.filter(name='supervisor').exists()

@register.inclusion_tag('chat/modal.html', takes_context=True)
def chat_modal(context):
    """
    Renderiza el modal del chat con el contexto necesario.
    Pasa la lista de asesores si el usuario es supervisor.
    """
    request = context['request']
    asesores = []
    # Reutilizamos el filtro 'es_supervisor' para mantener la lógica centralizada
    if es_supervisor(request.user):
        asesores = User.objects.filter(groups__name='asesor', is_active=True).order_by('first_name', 'last_name')
    return {'asesores': asesores, 'request': request}
