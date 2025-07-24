import json
import os

def format_transcript_as_script(json_input):
    """
    Lee un archivo JSON de transcripción o procesa directamente un diccionario JSON
    y lo formatea como un guion con marcas de tiempo.

    Args:
        json_input: Puede ser una ruta de archivo (str) o un diccionario con datos JSON ya cargados.

    Returns:
        str: Una cadena de texto con el guion formateado, o un mensaje de error con diagnóstico.
    """
    data = None
    try:
        # Determinar si el input es una ruta de archivo o un diccionario
        if isinstance(json_input, str):
            # Es una ruta de archivo
            if not os.path.exists(json_input):
                return f"[Error] Archivo no encontrado: {json_input}"
                
            with open(json_input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif isinstance(json_input, dict):
            # Es un diccionario ya cargado
            data = json_input
        else:
            return f"[Error] Tipo de entrada no válido: {type(json_input)}"
    except FileNotFoundError:
        return f"[Error] Archivo no encontrado: {json_input}"
    except json.JSONDecodeError:
        return f"[Error] El archivo no es un JSON válido: {json_input}"
    except Exception as e:
        return f"[Error] No se pudo procesar la entrada: {str(e)}"

    # Diagnóstico completo de la estructura
    if not data:
        return "[Error] No hay datos para procesar"
    
    print(f"⚙️ Estructura del JSON: {list(data.keys()) if isinstance(data, dict) else 'No es un diccionario'}")    
    
    # Intentar diferentes rutas para encontrar los segmentos
    segments = None
    if "output" in data:
        if "segments" in data["output"]:
            # Estructura estándar: output.segments
            segments = data["output"]["segments"]
            print("✅ Se encontraron segmentos en la ruta 'output.segments'")
        elif isinstance(data["output"], str):
            # Estructura de texto completo en output
            text = data["output"].strip()
            if text:
                print("✅ Se encontró texto completo en 'output'")
                return text  # Devolver el texto tal cual
    elif "segments" in data:
        # Estructura alternativa: directamente segments
        segments = data["segments"]
        print("✅ Se encontraron segmentos en la ruta 'segments'")
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "text" in data[0]:
        # Es una lista directa de segmentos
        segments = data
        print("✅ Se encontró una lista directa de segmentos")
    
    if not segments:
        print("❌ No se encontraron segmentos en ninguna ruta conocida")
        # Último intento: buscar campos de texto en cualquier estructura
        if isinstance(data, dict):
            # Si hay alguna clave 'text' o 'transcript' en el diccionario
            for key in ['text', 'transcript', 'transcription']:
                if key in data and isinstance(data[key], str) and data[key].strip():
                    print(f"✅ Se encontró texto en la clave '{key}'")
                    return data[key].strip()
        return "[Advertencia] No se encontraron segmentos de transcripción en el archivo"

    script_lines = []

    # Iterar a través de cada segmento y formatearlo
    for segment in segments:
        start_time = 0
        text = ""
        
        # Intentar diferentes formatos de segmentos
        if isinstance(segment, dict):
            # Buscar el tiempo de inicio en diferentes claves posibles
            for key in ['start', 'start_time', 'timestamp', 'time']:
                if key in segment:
                    start_time = float(segment[key]) if segment[key] is not None else 0
                    break
                    
            # Buscar el texto en diferentes claves posibles
            for key in ['text', 'content', 'transcript']:
                if key in segment and segment[key]:
                    text = segment[key].strip()
                    break
        elif isinstance(segment, str):
            # Si el segmento es directamente una cadena de texto
            text = segment.strip()
        
        if not text:
            continue
            
        # Convertir el tiempo de inicio a formato HH:MM:SS
        hours, remainder = divmod(start_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        # Agregar línea formateada
        script_lines.append(f"[{formatted_time}] {text}")

    if script_lines:
        return "\n".join(script_lines)
    else:
        # Si llegamos hasta aquí y no hay líneas, intentar devolver cualquier texto encontrado
        if isinstance(data, dict) and "output" in data and isinstance(data["output"], str):
            return data["output"].strip()
        return "[Advertencia] No se pudo generar la transcripción formateada"
