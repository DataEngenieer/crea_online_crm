import requests
import time
import json
import os
from requests.exceptions import RequestException

REPLICATE_TOKEN = os.getenv('REPLICATE_TOKEN')

def _make_request_with_retry(method, url, max_retries=3, backoff_factor=2, **kwargs):
    """
    Realiza una petición HTTP con reintentos y espera exponencial en caso de fallo.
    """
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            print(f"Error en la petición ({attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"Reintentando en {sleep_time} segundos...")
                time.sleep(sleep_time)
            else:
                print("Se alcanzó el máximo de reintentos. Falló la operación.")
                raise

def transcribir_audio(file_path):
    """
    Orquesta el proceso de transcripción de un archivo de audio usando la API de Replicate,
    implementando reintentos para mayor robustez.
    """
    # 1️⃣ Subir el archivo de audio
    url_upload = "https://api.replicate.com/v1/files"
    headers = {"Authorization": f"Bearer {REPLICATE_TOKEN}"}
    
    with open(file_path, "rb") as f:
        files = {"content": (os.path.basename(file_path), f, "application/octet-stream")}
        print("Subiendo archivo de audio para transcripción...")
        resp = _make_request_with_retry('post', url_upload, headers=headers, files=files)
    
    file_url = resp.json()["urls"]["get"]
    print(f"Archivo subido exitosamente: {file_url}")

    # 2️⃣ Crear la predicción
    model_version = "84d2ad2d6194fe98a17d2b60bef1c7f910c46b2f6fd38996ca457afd9c8abfcb"
    url_pred = "https://api.replicate.com/v1/predictions"
    payload = {
        "version": model_version,
        "input": {
            "audio_file": file_url,
            "language": "es",
            "batch_size": 64,
            "temperature": 0,
            "vad_onset": 0.5,
            "vad_offset": 0.363,
            "align_output": True,
            "diarization": False,
            "debug": True
        }
    }
    # Usamos un timeout largo y la cabecera 'wait' para que la API espere el resultado.
    headers.update({"Content-Type": "application/json", "Prefer": "wait"})
    
    print("Creando predicción de transcripción (esto puede tardar)...")
    # Un timeout generoso para la predicción, ya que 'wait' puede tardar.
    resp = _make_request_with_retry('post', url_pred, headers=headers, data=json.dumps(payload), timeout=600)
    prediction = resp.json()
    print("Predicción inicial recibida.")

    # 3️⃣ Esperar a que la predicción termine (sondeo como fallback)
    # Aunque 'Prefer: wait' debería ser síncrono, si la tarea es muy larga, puede devolver
    # una respuesta antes de tiempo. El sondeo asegura que esperemos el resultado final.
    prediction_id = prediction['id']
    url_get_prediction = f"{url_pred}/{prediction_id}"

    while prediction["status"] not in ("succeeded", "failed"):
        wait_time = 5
        print(f"Estado de la predicción: {prediction['status']}. Esperando {wait_time}s para volver a consultar...")
        time.sleep(wait_time)
        resp = _make_request_with_retry('get', url_get_prediction, headers=headers)
        prediction = resp.json()

    if prediction["status"] == "failed":
        error_detail = prediction.get('error')
        print(f"La transcripción falló: {error_detail}")
        raise Exception(f"Fallo en la transcripción de Replicate: {error_detail}")

    # Extraer estadísticas de uso de tokens si están disponibles
    metrics = prediction.get('metrics', {})
    tokens_entrada = metrics.get('input_token_count', 0)
    tokens_salida = metrics.get('output_token_count', 0)
    tiempo_procesamiento = metrics.get('total_duration', 0)

    print("Transcripción completada exitosamente.")
    return {
        "resultado": prediction,
        "estadisticas": {
            "tokens_entrada": tokens_entrada,
            "tokens_salida": tokens_salida,
            "tokens_totales": tokens_entrada + tokens_salida,
            "tiempo_procesamiento": tiempo_procesamiento
        }
    }
