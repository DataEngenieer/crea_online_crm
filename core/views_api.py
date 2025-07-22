from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def check_session(request):
    """
    Vista API para verificar si el usuario está autenticado.
    Retorna un JSON con el estado de autenticación.
    Esta vista es llamada periódicamente por el script session_checker.js
    para verificar si la sesión sigue activa.
    """
    return JsonResponse({
        'authenticated': request.user.is_authenticated
    })