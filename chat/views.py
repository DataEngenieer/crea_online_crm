from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage
import json
from django.utils import timezone
from django.db.models import Q


@login_required
@require_POST
def enviar_mensaje(request):
    data = json.loads(request.body)
    mensaje = data.get('mensaje', '').strip()
    remitente = request.user
    # Si el usuario es asesor, el destinatario es el primer supervisor encontrado
    if remitente.groups.filter(name='asesor').exists():
        supervisores = User.objects.filter(groups__name='supervisor')
        if not supervisores.exists():
            return JsonResponse({'error': 'No hay supervisores disponibles'}, status=400)
        destinatario = supervisores.first()
    else:
        # Si es supervisor, puede responder solo a asesores (en UI se puede elegir)
        destinatario_id = data.get('destinatario_id')
        if destinatario_id:
            try:
                destinatario = User.objects.get(id=destinatario_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Asesor no encontrado'}, status=400)
        else:
            return JsonResponse({'error': 'Debe indicar un destinatario'}, status=400)
    ChatMessage.objects.create(remitente=remitente, destinatario=destinatario, mensaje=mensaje)
    return JsonResponse({'status': 'ok'})

@login_required
def obtener_mensajes(request):
    user = request.user
    # Si es asesor, solo ve mensajes entre él y supervisores, y mensajes masivos
    if user.groups.filter(name='asesor').exists():
        supervisores = User.objects.filter(groups__name='supervisor')
        mensajes = ChatMessage.objects.filter(
            (Q(remitente=user) & Q(destinatario__in=supervisores)) |
            (Q(remitente__in=supervisores) & Q(destinatario=user)) |
            (Q(masivo=True))
        ).order_by('timestamp')
    else:
        # Si es supervisor, ve todos sus mensajes y los masivos enviados
        asesores = User.objects.filter(groups__name='asesor')
        mensajes = ChatMessage.objects.filter(
            (Q(remitente=user) & Q(destinatario__in=asesores)) |
            (Q(remitente__in=asesores) & Q(destinatario=user)) |
            (Q(masivo=True))
        ).order_by('timestamp')
    mensajes_json = [
        {
            'remitente': m.remitente.get_full_name() or m.remitente.username,
            'mensaje': m.mensaje,
            'timestamp': timezone.localtime(m.timestamp).strftime('%d/%m/%Y %H:%M'),
            'masivo': m.masivo
        } for m in mensajes
    ]
    return JsonResponse({'mensajes': mensajes_json})

@login_required
@require_POST
def enviar_masivo(request):
    user = request.user
    if not (user.groups.filter(name='supervisor').exists() or user.is_superuser):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    data = json.loads(request.body)
    mensaje = data.get('mensaje', '').strip()
    asesores = User.objects.filter(groups__name='asesor')
    for asesor in asesores:
        ChatMessage.objects.create(remitente=user, destinatario=asesor, mensaje=mensaje, masivo=True)
    return JsonResponse({'status': 'ok'})
