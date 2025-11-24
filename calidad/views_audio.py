import os
import io
import base64
import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para matplotlib
import matplotlib.pyplot as plt
import requests
import tempfile
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Speech
from .models_upgrade import AuditoriaUpgrade

def generar_grafico_onda(audio_source):
    """
    Genera una imagen de la forma de onda del audio y la devuelve como base64.
    
    Args:
        audio_source (str): Puede ser una ruta local o una URL de MinIO
    
    Returns:
        str: Imagen en formato base64 o None si hay error
    """
    temp_file = None
    try:
        # Determinar si es una URL o una ruta local
        if audio_source.startswith(('http://', 'https://')):
            # Es una URL de MinIO, descargar temporalmente
            response = requests.get(audio_source, timeout=30)
            response.raise_for_status()
            
            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(response.content)
            temp_file.close()
            
            audio_path = temp_file.name
        else:
            # Es una ruta local
            audio_path = audio_source
        
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
    finally:
        # Limpiar archivo temporal si se creó
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error al eliminar archivo temporal: {str(e)}")

def obtener_grafico_onda(request, speech_id):
    """
    Vista que devuelve la imagen de la forma de onda de un audio.
    Funciona tanto con archivos locales como con archivos en MinIO.
    """
    try:
        speech = get_object_or_404(Speech, id=speech_id)
        
        # Obtener la URL del audio (MinIO o local)
        audio_url = speech.get_audio_url()
        
        if not audio_url:
            return JsonResponse({'error': 'No hay archivo de audio disponible'}, status=404)
        
        # Si es una URL local, convertir a ruta absoluta
        if not audio_url.startswith(('http://', 'https://')):
            audio_path = os.path.join(settings.MEDIA_ROOT, str(speech.audio))
            if not os.path.exists(audio_path):
                return JsonResponse({'error': 'El archivo de audio no existe'}, status=404)
            audio_source = audio_path
        else:
            # Es una URL de MinIO
            audio_source = audio_url
        
        # Generar el gráfico de onda
        image_base64 = generar_grafico_onda(audio_source)
        
        if not image_base64:
            return JsonResponse({'error': 'Error al generar la forma de onda'}, status=500)
        
        return JsonResponse({
            'success': True,
            'waveform': f"data:image/png;base64,{image_base64}",
            'duration': speech.duracion_segundos,
            'audio_url': audio_url,
            'storage_type': 'minio' if speech.subido_a_minio else 'local'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def obtener_grafico_onda_upgrade(request, auditoria_id):
    try:
        auditoria = get_object_or_404(AuditoriaUpgrade, id=auditoria_id)
        if not auditoria.subido_a_minio or not auditoria.minio_url:
            return JsonResponse({'error': 'No hay archivo de audio disponible'}, status=404)
        audio_source = auditoria.minio_url
        image_base64 = generar_grafico_onda(audio_source)
        if not image_base64:
            return JsonResponse({'error': 'Error al generar la forma de onda'}, status=500)
        return JsonResponse({
            'success': True,
            'waveform': f"data:image/png;base64,{image_base64}",
            'duration': auditoria.duracion_segundos,
            'audio_url': auditoria.minio_url,
            'storage_type': 'minio'
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

def obtener_url_audio(request, speech_id):
    """
    Vista que devuelve la URL del archivo de audio.
    Prioriza MinIO sobre almacenamiento local.
    """
    try:
        speech = get_object_or_404(Speech, id=speech_id)
        
        audio_url = speech.get_audio_url()
        
        if not audio_url:
            return JsonResponse({'error': 'No hay archivo de audio disponible'}, status=404)
        
        return JsonResponse({
            'success': True,
            'audio_url': audio_url,
            'storage_type': 'minio' if speech.subido_a_minio else 'local',
            'duration': speech.duracion_segundos,
            'size_mb': speech.tamano_archivo_mb
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def resubir_a_minio(request, speech_id):
    """
    Vista para forzar la subida de un archivo a MinIO.
    Útil para migrar archivos existentes.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        speech = get_object_or_404(Speech, id=speech_id)
        
        if speech.subido_a_minio:
            return JsonResponse({
                'success': True,
                'message': 'El archivo ya está en MinIO',
                'url': speech.minio_url
            })
        
        if not speech.audio:
            return JsonResponse({'error': 'No hay archivo de audio para subir'}, status=400)
        
        # Forzar subida a MinIO
        speech.subido_a_minio = False  # Resetear para forzar subida
        speech._subir_audio_a_minio()
        
        if speech.subido_a_minio:
            speech.save(update_fields=['minio_url', 'minio_object_name', 'subido_a_minio', 'fecha_actualizacion'])
            return JsonResponse({
                'success': True,
                'message': 'Archivo subido exitosamente a MinIO',
                'url': speech.minio_url
            })
        else:
            return JsonResponse({'error': 'Error al subir archivo a MinIO'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
