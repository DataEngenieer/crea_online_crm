from django import template
from django.contrib.auth.models import Group
from django.template.loader import render_to_string

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si el usuario pertenece a un grupo específico.
    
    Uso en plantillas: 
    {% if user|has_group:"Nombre del Grupo" %}
        Contenido solo visible para miembros del grupo
    {% endif %}
    """
    try:
        # Primero verifica si el usuario está autenticado
        if not user.is_authenticated:
            return False
        
        # Verifica si el usuario pertenece al grupo
        return Group.objects.filter(name=group_name).filter(user=user).exists()
    except:
        return False

@register.simple_tag(takes_context=True)
def telefonica_sidebar_menu(context):
    """
    Renderiza el menú lateral de Telefónica.
    
    Uso en plantillas:
    {% load telefonica_extras %}
    {% telefonica_sidebar_menu %}
    """
    return render_to_string('telefonica/includes/sidebar_menu.html', context.flatten())