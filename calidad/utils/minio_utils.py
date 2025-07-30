import os
import logging
from django.conf import settings
from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename
from urllib.parse import urlparse

# Configurar logger
logger = logging.getLogger(__name__)

def get_minio_client():
    """
    Crea y retorna un cliente de MinIO configurado con las variables de entorno.
    
    Returns:
        Minio: Cliente de MinIO configurado
    """
    try:
        # Obtener configuración desde variables de entorno
        endpoint = getattr(settings, 'MINIO_ENDPOINT', '')
        access_key = getattr(settings, 'MINIO_ACCESS_KEY', '')
        secret_key = getattr(settings, 'MINIO_SECRET_KEY', '')
        
        logger.info(f"[MINIO-CLIENT] Configuración MinIO:")
        logger.info(f"[MINIO-CLIENT] Endpoint: {endpoint}")
        logger.info(f"[MINIO-CLIENT] Access Key: {access_key[:10]}..." if access_key else "[MINIO-CLIENT] Access Key: NO_CONFIGURADO")
        logger.info(f"[MINIO-CLIENT] Secret Key: {'*' * 10}..." if secret_key else "[MINIO-CLIENT] Secret Key: NO_CONFIGURADO")
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("Faltan variables de configuración de MinIO")
        
        # Parsear el endpoint para determinar si es seguro
        parsed_url = urlparse(endpoint)
        secure = parsed_url.scheme == 'https'
        
        # Remover el esquema del endpoint para MinIO
        clean_endpoint = parsed_url.netloc or parsed_url.path
        
        logger.info(f"[MINIO-CLIENT] Endpoint parseado: {clean_endpoint}")
        logger.info(f"[MINIO-CLIENT] Conexión segura: {secure}")
        
        # Crear cliente MinIO
        logger.info(f"[MINIO-CLIENT] Creando cliente MinIO...")
        client = Minio(
            clean_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        logger.info(f"[MINIO-CLIENT] ✅ Cliente MinIO creado exitosamente para endpoint: {clean_endpoint}")
        return client
        
    except Exception as e:
        logger.error(f"[MINIO-CLIENT] ❌ Error al crear cliente MinIO: {str(e)}")
        import traceback
        logger.error(f"[MINIO-CLIENT] Traceback: {traceback.format_exc()}")
        raise

def subir_a_minio(archivo, nombre_personalizado=None, carpeta="audios", bucket_type="MINIO_BUCKET_NAME_LLAMADAS"):
    """
    Sube un archivo a MinIO con validaciones y configuración de chunks.
    
    Args:
        archivo: Archivo de Django (UploadedFile)
        nombre_personalizado (str, optional): Nombre personalizado para el archivo
        carpeta (str): Carpeta dentro del bucket donde guardar el archivo
        bucket_type (str): Tipo de bucket a usar del diccionario MINIO_BUCKET_NAME
    
    Returns:
        dict: Diccionario con información del archivo subido
            {
                'success': bool,
                'url': str,
                'filename': str,
                'size': int,
                'error': str (si hay error)
            }
    """
    try:
        logger.info(f"[MINIO-UTILS] Iniciando subida a MinIO")
        logger.info(f"[MINIO-UTILS] Parámetros: nombre_personalizado={nombre_personalizado}, carpeta={carpeta}, bucket_type={bucket_type}")
        
        # Validar que el archivo existe y tiene nombre
        if not archivo or not hasattr(archivo, 'name') or not archivo.name:
            error_msg = 'Archivo inválido o sin nombre'
            logger.error(f"[MINIO-UTILS] {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        logger.info(f"[MINIO-UTILS] Archivo válido: {archivo.name}")
        
        # Obtener configuración del bucket desde el diccionario
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get(bucket_type, 'default-bucket')
        
        logger.info(f"[MINIO-UTILS] Configuración de buckets: {bucket_dict}")
        logger.info(f"[MINIO-UTILS] Bucket seleccionado: {bucket_name}")
        
        if not bucket_name or bucket_name == 'default-bucket':
            logger.warning(f"[MINIO-UTILS] Bucket type '{bucket_type}' no encontrado en configuración, usando default")
            bucket_name = 'default-bucket'
        
        # Crear cliente MinIO
        logger.info(f"[MINIO-UTILS] Creando cliente MinIO...")
        client = get_minio_client()
        logger.info(f"[MINIO-UTILS] Cliente MinIO creado exitosamente")
        
        # Verificar si el bucket existe, si no, crearlo
        logger.info(f"[MINIO-UTILS] Verificando existencia del bucket: {bucket_name}")
        if not client.bucket_exists(bucket_name):
            logger.info(f"[MINIO-UTILS] Bucket no existe, creándolo...")
            client.make_bucket(bucket_name)
            logger.info(f"[MINIO-UTILS] Bucket '{bucket_name}' creado")
        else:
            logger.info(f"[MINIO-UTILS] Bucket '{bucket_name}' ya existe")
        
        # Generar nombre seguro del archivo
        if nombre_personalizado:
            # Obtener extensión del archivo original
            _, extension = os.path.splitext(archivo.name)
            filename = secure_filename(f"{nombre_personalizado}{extension}")
            logger.info(f"[MINIO-UTILS] Nombre personalizado generado: {filename}")
        else:
            filename = secure_filename(archivo.name)
            logger.info(f"[MINIO-UTILS] Usando nombre original: {filename}")
        
        # Construir la ruta completa en el bucket
        object_name = f"{carpeta}/{filename}" if carpeta else filename
        logger.info(f"[MINIO-UTILS] Ruta completa en bucket: {object_name}")
        
        # Obtener el tamaño del archivo
        archivo.seek(0, 2)  # Ir al final del archivo
        file_size = archivo.tell()
        archivo.seek(0)  # Volver al inicio
        logger.info(f"[MINIO-UTILS] Tamaño del archivo: {file_size} bytes")
        
        # Subir archivo con configuración de chunks de 10MB
        logger.info(f"[MINIO-UTILS] Iniciando subida del archivo...")
        client.put_object(
            bucket_name,
            object_name,
            archivo,
            length=file_size,
            part_size=10*1024*1024  # 10MB chunks
        )
        logger.info(f"[MINIO-UTILS] Archivo subido exitosamente al bucket")
        
        # Construir URL pública del archivo
        endpoint = getattr(settings, 'MINIO_ENDPOINT', '')
        
        # Remover puerto :443 para HTTPS ya que es implícito
        from urllib.parse import urlparse
        parsed_endpoint = urlparse(endpoint)
        if parsed_endpoint.scheme == 'https' and parsed_endpoint.port == 443:
            # Reconstruir URL sin el puerto para HTTPS
            clean_endpoint = f"{parsed_endpoint.scheme}://{parsed_endpoint.hostname}"
        elif parsed_endpoint.scheme == 'http' and parsed_endpoint.port == 80:
            # Reconstruir URL sin el puerto para HTTP
            clean_endpoint = f"{parsed_endpoint.scheme}://{parsed_endpoint.hostname}"
        else:
            # Mantener el endpoint original si no es puerto estándar
            clean_endpoint = endpoint
        
        public_url = f"{clean_endpoint}/{bucket_name}/{object_name}"
        logger.info(f"[MINIO-UTILS] URL pública generada: {public_url}")
        
        logger.info(f"[MINIO-UTILS] ✅ Archivo subido exitosamente: {object_name}")
        
        return {
            'success': True,
            'url': public_url,
            'filename': filename,
            'object_name': object_name,
            'size': file_size
        }
        
    except S3Error as e:
        error_msg = f"Error de MinIO: {str(e)}"
        logger.error(f"[MINIO-UTILS] ❌ {error_msg}")
        import traceback
        logger.error(f"[MINIO-UTILS] Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Error al subir archivo: {str(e)}"
        logger.error(f"[MINIO-UTILS] ❌ {error_msg}")
        import traceback
        logger.error(f"[MINIO-UTILS] Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': error_msg
        }

def eliminar_de_minio(object_name, bucket_type="MINIO_BUCKET_NAME_LLAMADAS"):
    """
    Elimina un archivo de MinIO.
    
    Args:
        object_name (str): Nombre del objeto en MinIO (incluye carpeta si aplica)
        bucket_type (str): Tipo de bucket a usar del diccionario MINIO_BUCKET_NAME
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Obtener configuración del bucket desde el diccionario
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get(bucket_type, 'default-bucket')
        client = get_minio_client()
        
        client.remove_object(bucket_name, object_name)
        
        logger.info(f"Archivo eliminado exitosamente: {object_name}")
        return {
            'success': True,
            'message': f'Archivo {object_name} eliminado exitosamente'
        }
        
    except S3Error as e:
        error_msg = f"Error de MinIO al eliminar: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Error al eliminar archivo: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }

def obtener_url_descarga(object_name, expiry_days=7, bucket_type="MINIO_BUCKET_NAME_LLAMADAS"):
    """
    Genera una URL de descarga temporal para un archivo en MinIO.
    
    Args:
        object_name (str): Nombre del objeto en MinIO
        expiry_days (int): Días de validez de la URL (default: 7)
        bucket_type (str): Tipo de bucket a usar del diccionario MINIO_BUCKET_NAME
    
    Returns:
        str: URL de descarga temporal o None si hay error
    """
    try:
        # Obtener configuración del bucket desde el diccionario
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get(bucket_type, 'default-bucket')
        client = get_minio_client()
        
        # Generar URL con expiración
        from datetime import timedelta
        url = client.presigned_get_object(
            bucket_name,
            object_name,
            expires=timedelta(days=expiry_days)
        )
        
        return url
        
    except Exception as e:
        logger.error(f"Error al generar URL de descarga: {str(e)}")
        return None