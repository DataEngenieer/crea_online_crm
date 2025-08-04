import os
import json
import requests
from typing import Dict, Any
from django.db import transaction
from ..models import Auditoria, MatrizCalidad, DetalleAuditoria

class AnalizadorTranscripciones:
    """
    Clase para analizar transcripciones de llamadas utilizando un modelo de IA.
    """
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("API key de DeepSeek no encontrada en las variables de entorno.")
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def evaluar_calidad_llamada(self, transcripcion: str) -> Dict[str, Any]:
        """
        Evalúa la calidad de una llamada a partir de su transcripción.
        """
        # Validar que la transcripción no esté vacía
        if not transcripcion or not isinstance(transcripcion, str) or transcripcion.strip() == "":
            return {"error": "No se proporcionó una transcripción válida para analizar"}
        
        # Si la transcripción comienza con '[Error' o '[Advertencia]', devolver un error
        if transcripcion.strip().startswith("[Error") or transcripcion.strip().startswith("[Advertencia]"):
            return {"error": f"Transcripción inválida: {transcripcion}"}
        
        instrucciones = self._construir_instrucciones()

        # --- DEBUG: Imprimir el prompt para verificación ---
        print("="*50)
        print("PROMPT ENVIADO A LA IA:")
        print(instrucciones)
        print("="*50)
        
        # Imprimir un fragmento de la transcripción para verificación
        #preview_length = min(len(transcripcion), 200)
        #print(f"PRIMEROS {preview_length} CARACTERES DE LA TRANSCRIPCIÓN:")
        #print(transcripcion[:preview_length] + ("..." if len(transcripcion) > preview_length else ""))
        print("="*50)

        return self._enviar_solicitud_ia(transcripcion, instrucciones)

    def _construir_instrucciones(self : str = None) -> str:
        """
        Construye dinámicamente el prompt para el modelo de IA con las instrucciones de evaluación
        basadas en los indicadores activos de la Matriz de Calidad.
        """
        from collections import defaultdict

        indicadores_activos = MatrizCalidad.objects.filter(activo=True).order_by('categoria', 'id')
        
        if not indicadores_activos.exists():
            # Devuelve un mensaje de error o un prompt básico si no hay indicadores
            return "No hay indicadores de calidad activos para evaluar. Por favor, configure la Matriz de Calidad."

        categorias = defaultdict(list)
        for indicador in indicadores_activos:
            categorias[indicador.categoria].append(indicador)

        indicadores_texto = []
        contador_global = 1
        for categoria_nombre, indicadores_lista in categorias.items():
            indicadores_texto.append(f"\nCATEGORÍA: {categoria_nombre.upper()}")
            for indicador in indicadores_lista:
                ponderacion_str = f"({int(indicador.ponderacion)}%)"
                indicadores_texto.append(f"{contador_global}. {indicador.indicador} {ponderacion_str}")
                contador_global += 1
        
        indicadores_str = "\n".join(indicadores_texto)


        return f"""Situacion: Eres un experto analista de calidad en un call center para llamadas de ventas outbound en telefonica movistar. 
                Tarea: Realizar un análisis exhaustivo y detallado de una transcripción de llamada de ventas, 
                evaluando sistemáticamente los siguientes indicadores de calidad:

            {indicadores_str}

            FORMATO DE RESPUESTA REQUERIDO (JSON):
            {{
                "evaluacion": [
                    {{
                        "categoria": "Nombre de la categoría",
                        "indicador": "Nombre completo del indicador",
                        "ponderacion": "XX%",
                        "evaluacion": "Análisis detallado del cumplimiento",
                        "cumple": true/false,
                        "subitems": []
                    }}
                ],
                "puntaje_total": "XX.XX%",
                "resumen": "Resumen general de la evaluación"
            }}

            INSTRUCCIONES CRÍTICAS:
            1. DEBES evaluar TODOS Y CADA UNO de los {contador_global-1} indicadores listados arriba.
            2. Para cada indicador, determina si se cumple (true) o no (false).
            3. Justifica cada evaluación en el campo 'evaluacion'.
            4. Los nombres de los indicadores deben ser tal cual como los entrega arriba, no puedes cambiar ni un 
            solo caracter del indicador por q despues el json no lo reconoce el siguiente sistema
            5. Si un indicador no se puede evaluar por falta de información, márcalo como 'true' y explica por qué.
            6. Calcula el puntaje total considerando las ponderaciones.
            7. Tu respuesta JSON debe contener exactamente {contador_global-1} elementos en el array 'evaluacion'.
            8. Tu evaluación debe ser completamente objetiva, sin sesgos personales, centrándote exclusivamente en los hechos y la transcripcion de la llamada.

            IMPORTANTE: Responde ÚNICAMENTE con el JSON válido, sin comentarios adicionales. NO omitas ningún indicador.

            La transcripcion a analizar es la siguiente:
            
            """

    def _enviar_solicitud_ia(self, texto: str, instrucciones: str) -> Dict[str, Any]:
        """
        Envía la solicitud al API de DeepSeek y procesa la respuesta.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": instrucciones},
                    {"role": "user", "content": texto}
                ],
                "temperature": 0.1,
                #"max_tokens": 6000,
                "response_format": {"type": "json_object"}
            }
            print(payload)
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            contenido = response.json()
            respuesta_texto = contenido['choices'][0]['message']['content']
            
            return self._procesar_respuesta(respuesta_texto)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red o API: {e}")
            return {"error": f"Error en la comunicación con la IA: {str(e)}"}
        except Exception as e:
            print(f"❌ Error inesperado en la evaluación: {e}")
            return {"error": f"Error inesperado en la evaluación: {str(e)}"}

    def _procesar_respuesta(self, contenido: str) -> Dict[str, Any]:
        """
        Parsea la respuesta JSON del modelo de IA.
        """
        try:
            if '```json' in contenido:
                contenido = contenido.split('```json')[1].split('```')[0].strip()
            return json.loads(contenido)
        except Exception as e:
            print(f"❌ Error procesando la respuesta JSON de la IA: {e}")
            return {"error": f"Error procesando respuesta: {str(e)}", "respuesta_cruda": contenido[:1000]}

def autocompletar_auditoria_desde_analisis(auditoria: Auditoria, analisis_json: dict):
    """
    Toma el resultado del análisis de IA y lo usa para llenar los detalles
    de una auditoría de calidad de forma atómica.
    """
    if not isinstance(analisis_json, dict) or 'evaluacion' not in analisis_json:
        print(f"[Auditoría {auditoria.id}] ❌ Análisis JSON inválido o vacío. No se puede autocompletar.")
        return

    try:
        with transaction.atomic():
            evaluaciones = analisis_json.get('evaluacion', [])
            
            # Obtener todos los indicadores activos
            indicadores_activos = MatrizCalidad.objects.filter(activo=True)
            
            # Se crea un diccionario de búsqueda normalizando las claves (minúsculas y sin espacios extra)
            indicadores_db = {
                item.indicador.strip().lower(): item 
                for item in indicadores_activos
            }
            
            # Crear un set de indicadores procesados por la IA
            indicadores_procesados = set()

            # Procesar las evaluaciones devueltas por la IA
            for item_evaluado in evaluaciones:
                nombre_indicador_raw = item_evaluado.get('indicador')
                if not nombre_indicador_raw:
                    continue
                
                nombre_indicador_normalizado = nombre_indicador_raw.strip().lower()
                indicadores_procesados.add(nombre_indicador_normalizado)

                if nombre_indicador_normalizado in indicadores_db:
                    indicador_obj = indicadores_db[nombre_indicador_normalizado]
                    DetalleAuditoria.objects.update_or_create(
                        auditoria=auditoria,
                        indicador=indicador_obj,
                        defaults={
                            'cumple': item_evaluado.get('cumple', False),
                            'observaciones': item_evaluado.get('evaluacion', '')
                        }
                    )
                else:
                    print(f"[Auditoría {auditoria.id}] ⚠️  Advertencia: Indicador '{nombre_indicador_raw}' no encontrado en la Matriz de Calidad.")
            
            # Verificar indicadores faltantes y crearlos con cumple=False
            indicadores_faltantes = 0
            for indicador_obj in indicadores_activos:
                nombre_normalizado = indicador_obj.indicador.strip().lower()
                if nombre_normalizado not in indicadores_procesados:
                    DetalleAuditoria.objects.update_or_create(
                        auditoria=auditoria,
                        indicador=indicador_obj,
                        defaults={
                            'cumple': False,
                            'observaciones': 'No evaluado por la IA - Indicador faltante en la respuesta automática'
                        }
                    )
                    indicadores_faltantes += 1
                    print(f"[Auditoría {auditoria.id}] ⚠️  Indicador faltante agregado: {indicador_obj.indicador}")
            
            if indicadores_faltantes > 0:
                print(f"[Auditoría {auditoria.id}] ⚠️  Se agregaron {indicadores_faltantes} indicadores faltantes con cumple=False")

            # Actualizar el resumen y puntaje de IA en la auditoría principal
            auditoria.puntaje_ia = analisis_json.get('puntaje_total', '')
            auditoria.resumen_ia = analisis_json.get('resumen', '')
            auditoria.save(update_fields=['puntaje_ia', 'resumen_ia'])
            
            # Forzar el recálculo del puntaje total basado en los nuevos detalles
            auditoria.calcular_puntaje_total() # Esta función ya guarda el modelo

            print(f"[Auditoría {auditoria.id}] ✅ Autocompletada con {len(evaluaciones)} indicadores de IA + {indicadores_faltantes} faltantes. Puntaje recalculado.")

    except Exception as e:
        print(f"[Auditoría {auditoria.id}] ❌ Error crítico al autocompletar la auditoría: {e}")
