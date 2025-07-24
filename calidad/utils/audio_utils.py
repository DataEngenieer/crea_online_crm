import os
import subprocess
import json
from datetime import datetime
from django.conf import settings
from pathlib import Path
import tempfile
import librosa
import soundfile as sf

def obtener_duracion_audio(ruta_archivo):
    """
    Obtiene la duración de un archivo de audio en segundos usando librosa
    """
    # Normalizar la ruta del archivo
    ruta_absoluta = os.path.abspath(ruta_archivo)
    
    if not os.path.exists(ruta_absoluta):
        print(f"Error: El archivo no existe en la ruta: {ruta_absoluta}")
        return 0.0
    
    print(f"Obteniendo duración del archivo: {ruta_absoluta}")
    print(f"Tamaño del archivo: {os.path.getsize(ruta_absoluta) / (1024 * 1024):.2f} MB")
    
    try:
        # Usar librosa para obtener la duración
        # load=False solo lee los metadatos, no carga todo el audio en memoria
        duration = librosa.get_duration(filename=ruta_absoluta)
        
        if duration > 0:
            print(f"Duración obtenida con librosa: {duration:.2f} segundos")
            return duration
        else:
            # Si librosa falla, intentar con soundfile
            print("Librosa devolvió duración 0, intentando con soundfile...")
            with sf.SoundFile(ruta_absoluta) as f:
                duration = len(f) / f.samplerate
                print(f"Duración obtenida con soundfile: {duration:.2f} segundos")
                return duration
                
    except Exception as e:
        print(f"Error al obtener duración con librosa/soundfile: {str(e)}")
        
        # Si todo falla, estimar basado en el tamaño del archivo
        try:
            tamano_bytes = os.path.getsize(ruta_absoluta)
            # Estimación aproximada: 1 minuto por cada 1MB (para audio MP3 de 128kbps)
            duracion_estimada = (tamano_bytes / (1024 * 1024)) * 0.5  # 0.5 minutos por MB
            print(f"Usando duración estimada: {duracion_estimada:.2f} segundos (basado en tamaño de archivo)")
            return duracion_estimada
        except Exception as e2:
            print(f"Error al estimar duración: {str(e2)}")
            print("Usando valor predeterminado de 60 segundos")
            return 60.0

def obtener_tamano_archivo_mb(ruta_archivo):
    """
    Obtiene el tamaño del archivo en MB.
    Devuelve 0.0 si hay algún error o si el archivo no existe.
    """
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo no existe en la ruta: {ruta_archivo}")
        return 0.0
        
    try:
        tamano_bytes = os.path.getsize(ruta_archivo)
        tamano_mb = tamano_bytes / (1024 * 1024)  # Convertir a MB
        print(f"Tamaño del archivo: {tamano_mb:.2f} MB")
        return tamano_mb
    except Exception as e:
        print(f"Error al obtener tamaño del archivo {ruta_archivo}: {str(e)}")
        return 0.0

def extraer_metadatos_audio(audio_path):
    """
    Extrae metadatos del archivo de audio usando ffprobe.
    Devuelve un diccionario con los metadatos o None si hay un error.
    """
    if not os.path.exists(audio_path):
        print(f"Error: No se puede extraer metadatos. El archivo no existe: {audio_path}")
        return None
        
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_path
        ]
        print(f"Extrayendo metadatos con comando: {' '.join(cmd)}")
        resultado = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if resultado.returncode == 0:
            metadatos = json.loads(resultado.stdout)
            print(f"Metadatos extraídos correctamente para {audio_path}")
            return metadatos
        else:
            print(f"Error al extraer metadatos: {resultado.stderr}")
            return None
    except Exception as e:
        print(f"Error al extraer metadatos: {e}")
    return {}