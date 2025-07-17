from django import template
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.forms.widgets import Input, Textarea, Select, CheckboxInput, RadioSelect

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

@register.filter(name='attr')
def set_attr(field, attr_string):
    """
    Establece atributos para un campo de formulario.
    
    Uso en plantillas:
    {{ form.field|attr:"class:form-control,placeholder:Ingrese texto,rows:4" }}
    
    Esto agregará los atributos class="form-control", placeholder="Ingrese texto" y rows="4" al campo.
    """
    if not field:
        return field
    
    attrs = {}
    pairs = attr_string.split(',')
    
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            attrs[key.strip()] = value.strip()
    
    # Si el campo ya tiene un widget, actualiza sus atributos
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        widget = field.field.widget
        if not widget.attrs:
            widget.attrs = {}
        
        for key, value in attrs.items():
            widget.attrs[key] = value
            
    return field