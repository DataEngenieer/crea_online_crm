import os
import io
import base64
import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para matplotlib
import matplotlib.pyplot as plt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Speech

def generar_grafico_onda(audio_path):
    """
    Genera una imagen de la forma de onda del audio y la devuelve como base64
    """
    try:
        # Cargar el archivo de audio
        y, sr = librosa.load(audio_path, sr=None)
        
        # Configurar la figura
        plt.figure(figsize=(12, 2))
        librosa.display.waveshow(y, sr=sr, color='#4e73df', alpha=0.8)
        
        # Personalizar el gráfico
        plt.axis('off')  # Ocultar ejes
        plt.tight_layout(pad=0)
        
        # Guardar la figura en un buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close()
        
        # Convertir la imagen a base64
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        
        return image_base64
    except Exception as e:
        print(f"Error al generar el gráfico de onda: {str(e)}")
        return None

def obtener_grafico_onda(request, speech_id):
    """
    Vista que devuelve la imagen de la forma de onda de un audio
    """
    try:
        speech = get_object_or_404(Speech, id=speech_id)
        
        if not speech.audio:
            return JsonResponse({'error': 'No hay archivo de audio disponible'}, status=404)
        
        audio_path = os.path.join(settings.MEDIA_ROOT, str(speech.audio))
        
        if not os.path.exists(audio_path):
            return JsonResponse({'error': 'El archivo de audio no existe'}, status=404)
        
        # Generar el gráfico de onda
        image_base64 = generar_grafico_onda(audio_path)
        
        if not image_base64:
            return JsonResponse({'error': 'Error al generar la forma de onda'}, status=500)
        
        return JsonResponse({
            'success': True,
            'waveform': f"data:image/png;base64,{image_base64}",
            'duration': speech.duracion_segundos
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def control_voz(request):
    """
    Vista para manejar comandos de voz
    """
    try:
        data = request.POST
        command = data.get('command', '').lower()
        speech_id = data.get('speech_id')
        
        if not speech_id:
            return JsonResponse({'error': 'ID de speech no proporcionado'}, status=400)
        
        response = {'success': True, 'message': ''}
        
        # Aquí podrías implementar lógica adicional basada en el comando de voz
        if 'reproducir' in command or 'play' in command:
            response['action'] = 'play'
            response['message'] = 'Reproduciendo audio'
        elif 'pausa' in command or 'pausar' in command or 'pausar' in command:
            response['action'] = 'pause'
            response['message'] = 'Audio pausado'
        elif 'detener' in command or 'stop' in command:
            response['action'] = 'stop'
            response['message'] = 'Audio detenido'
        elif 'adelantar' in command or 'avanzar' in command:
            response['action'] = 'forward'
            response['message'] = 'Avanzando 10 segundos'
        elif 'retroceder' in command or 'atrás' in command:
            response['action'] = 'rewind'
            response['message'] = 'Retrocediendo 10 segundos'
        else:
            response['success'] = False
            response['message'] = 'Comando no reconocido'
        
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)
