def telefonica_menu(request):
    """
    Contexto global para incluir variables relacionadas con la aplicación Telefónica
    en todas las plantillas del proyecto.
    
    Este procesador de contexto agrega:
    - show_telefonica_menu: Indica si se debe mostrar el menú de Telefónica
    """
    # Verificamos si el usuario está autenticado
    if request.user.is_authenticated:
        # Verificamos si el usuario pertenece a grupos relevantes para Telefónica
        groups = [g.name for g in request.user.groups.all()]
        telefonica_groups = ['Asesores', 'Backoffice']
        show_menu = any(group in telefonica_groups for group in groups)
        
        return {
            'show_telefonica_menu': show_menu,
        }
    
    return {
        'show_telefonica_menu': False,
    }