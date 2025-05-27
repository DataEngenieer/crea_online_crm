import fitz # PyMuPDF
from PyPDF2 import PdfWriter, PdfReader
import re
import os
from datetime import datetime
from django.core.files import File
from core.models import SolicitudCarga, Comprobante
from django.utils import timezone

# --- FUNCIÓN PRINCIPAL usando modelos Django ORM ---
def separar_comprobantes_pdf(ruta_pdf_consolidado: str, ruta_salida: str, cargado_por: str = "Sistema") -> dict:
    resultados = {
        "pdfs_generados": 0,
        "errores": [],
        "id_solicitud_carga": None
    }

    if not os.path.exists(ruta_salida):
        os.makedirs(ruta_salida)
        print(f"Directorio de salida '{ruta_salida}' creado.")

    try:
        nombre_original = os.path.basename(ruta_pdf_consolidado)
        pdf_documento_temp = fitz.open(ruta_pdf_consolidado)
        cantidad_paginas_original = pdf_documento_temp.page_count
        pdf_documento_temp.close()
        # Crear la solicitud de carga en el ORM
        solicitud = SolicitudCarga.objects.create(
            nombre_archivo_original=nombre_original,
            cantidad_paginas_original=cantidad_paginas_original,
            cantidad_comprobantes_separados=0,
            cargado_por=cargado_por,
            fecha_carga=timezone.now(),
            estado='Procesando'
        )
        resultados["id_solicitud_carga"] = solicitud.id
        print(f"Solicitud de carga registrada con ID: {solicitud.id}")
        pdf_documento = fitz.open(ruta_pdf_consolidado)
        num_paginas = pdf_documento.page_count
        patron_identificacion = re.compile(r"IDENTIFICACION\s*\n\s*(\d+)", re.IGNORECASE)
        patron_nombre = re.compile(r"NOMBRE\s*\n\s*\d+\s*\n\s*([^\n]+)", re.IGNORECASE)
        patron_fecha_pago = re.compile(r"Fecha de Pago:\s*(\d{2}/\d{2}/\d{4})")
        patron_periodo = re.compile(r"Periodo:.*?Al\s*(\d{2}/\d{2}/\d{4})")
        for i in range(num_paginas):
            pagina = pdf_documento.load_page(i)
            texto_pagina = pagina.get_text("text")
            id_empleado = "sin_id"
            nombre_empleado = "sin_nombre"
            fecha_pago = None
            mes_periodo = "mes_desconocido"
            match_id = patron_identificacion.search(texto_pagina)
            if match_id:
                id_empleado = match_id.group(1).strip()
            else:
                resultados["errores"].append(f"ID no encontrado en página {i+1}")
            match_nombre = patron_nombre.search(texto_pagina)
            if match_nombre:
                nombre_empleado = match_nombre.group(1).strip()
            else:
                resultados["errores"].append(f"Nombre no encontrado en página {i+1}")
            match_fecha_pago = patron_fecha_pago.search(texto_pagina)
            if match_fecha_pago:
                fecha_pago_str = match_fecha_pago.group(1).strip()
                try:
                    fecha_pago = datetime.strptime(fecha_pago_str, '%d/%m/%Y').date()
                except ValueError:
                    resultados["errores"].append(f"Formato de fecha de pago inválido en página {i+1}")
            else:
                resultados["errores"].append(f"Fecha de Pago no encontrada en página {i+1}")
            match_periodo = patron_periodo.search(texto_pagina)
            if match_periodo:
                fecha_fin_periodo_str = match_periodo.group(1).strip()
                try:
                    fecha_fin_periodo = datetime.strptime(fecha_fin_periodo_str, '%d/%m/%Y')
                    mes_periodo = fecha_fin_periodo.strftime('%Y_%m')
                except ValueError:
                    resultados["errores"].append(f"Formato de fecha de periodo inválido en página {i+1}")
            else:
                resultados["errores"].append(f"Periodo de pago no encontrado para nombre de archivo en página {i+1}")
            nombre_base_archivo = f"{id_empleado}_{nombre_empleado}_{mes_periodo}"
            nombre_base_archivo_limpio = re.sub(r'[^\w\s-]', '', nombre_base_archivo).strip().replace(' ', '_')
            nombre_base_archivo_limpio = nombre_base_archivo_limpio[:120]
            pdf_writer = PdfWriter()
            pdf_reader = PdfReader(ruta_pdf_consolidado)
            pdf_writer.add_page(pdf_reader.pages[i])
            nombre_archivo_salida = f"{nombre_base_archivo_limpio}_comprobante_{i+1}.pdf"
            ruta_completa_salida = os.path.join(ruta_salida, nombre_archivo_salida)
            with open(ruta_completa_salida, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
            resultados["pdfs_generados"] += 1
            
            # Registrar comprobante en el ORM - MODIFICADO
            comprobante_obj = Comprobante(
                id_solicitud=solicitud,
                identificacion_empleado=id_empleado,
                nombre_empleado=nombre_empleado,
                fecha_comprobante=fecha_pago,
                mes_periodo=mes_periodo,
                nombre_archivo_generado=nombre_archivo_salida # Usado para el nombre de descarga
            )
            # Asignar el archivo físico al FileField
            try:
                with open(ruta_completa_salida, 'rb') as pdf_file_content:
                    # El 'name' aquí es el nombre que tendrá el archivo en MEDIA_ROOT/comprobantes/
                    django_file = File(pdf_file_content, name=nombre_archivo_salida) 
                    comprobante_obj.archivo_comprobante = django_file
                    comprobante_obj.save()
            except IOError as e:
                resultados["errores"].append(f"Error al guardar archivo para {nombre_archivo_salida}: {e}")
                # Considerar si se debe decrementar pdfs_generados o marcar el comprobante como fallido
                # Por ahora, solo se registra el error.

        pdf_documento.close()
        # Actualizar solicitud de carga con resultados
        final_estado = 'Completado' if not resultados["errores"] else 'Con Errores'
        errores_str = "\n".join(resultados["errores"]) if resultados["errores"] else None
        solicitud.cantidad_comprobantes_separados = resultados["pdfs_generados"]
        solicitud.estado = final_estado
        solicitud.errores_detectados = errores_str
        solicitud.save()
    except FileNotFoundError:
        error_msg = f"Error: El archivo PDF '{ruta_pdf_consolidado}' no fue encontrado."
        print(error_msg)
        resultados["errores"].append(error_msg)
        if resultados["id_solicitud_carga"]:
            solicitud = SolicitudCarga.objects.get(id=resultados["id_solicitud_carga"])
            solicitud.estado = 'Fallido'
            solicitud.errores_detectados = error_msg
            solicitud.save()
    except Exception as e:
        error_msg = f"Ocurrió un error inesperado durante el procesamiento: {e}"
        print(error_msg)
        resultados["errores"].append(error_msg)
        if resultados["id_solicitud_carga"]:
            solicitud = SolicitudCarga.objects.get(id=resultados["id_solicitud_carga"])
            solicitud.estado = 'Fallido'
            solicitud.errores_detectados = error_msg
            solicitud.save()
    return resultados
