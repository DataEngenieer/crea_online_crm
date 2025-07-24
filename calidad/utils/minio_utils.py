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
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("Faltan variables de configuración de MinIO")
        
        # Parsear el endpoint para determinar si es seguro
        parsed_url = urlparse(endpoint)
        secure = parsed_url.scheme == 'https'
        
        # Remover el esquema del endpoint para MinIO
        clean_endpoint = parsed_url.netloc or parsed_url.path
        
        # Crear cliente MinIO
        client = Minio(
            clean_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        logger.info(f"Cliente MinIO creado exitosamente para endpoint: {clean_endpoint}")
        return client
        
    except Exception as e:
        logger.error(f"Error al crear cliente MinIO: {str(e)}")
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
        # Validar que el archivo existe y tiene nombre
        if not archivo or not hasattr(archivo, 'name') or not archivo.name:
            return {
                'success': False,
                'error': 'Archivo inválido o sin nombre'
            }
        
        # Obtener configuración del bucket desde el diccionario
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get(bucket_type, 'default-bucket')
        
        if not bucket_name or bucket_name == 'default-bucket':
            logger.warning(f"Bucket type '{bucket_type}' no encontrado en configuración, usando default")
            bucket_name = 'default-bucket'
        
        # Crear cliente MinIO
        client = get_minio_client()
        
        # Verificar si el bucket existe, si no, crearlo
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' creado")
        
        # Generar nombre seguro del archivo
        if nombre_personalizado:
            # Obtener extensión del archivo original
            _, extension = os.path.splitext(archivo.name)
            filename = secure_filename(f"{nombre_personalizado}{extension}")
        else:
            filename = secure_filename(archivo.name)
        
        # Construir la ruta completa en el bucket
        object_name = f"{carpeta}/{filename}" if carpeta else filename
        
        # Obtener el tamaño del archivo
        archivo.seek(0, 2)  # Ir al final del archivo
        file_size = archivo.tell()
        archivo.seek(0)  # Volver al inicio
        
        # Subir archivo con configuración de chunks de 10MB
        client.put_object(
            bucket_name,
            object_name,
            archivo,
            length=file_size,
            part_size=10*1024*1024  # 10MB chunks
        )
        
        # Construir URL pública del archivo
        endpoint = getattr(settings, 'MINIO_ENDPOINT', '')
        public_url = f"{endpoint}/{bucket_name}/{object_name}"
        
        logger.info(f"Archivo subido exitosamente: {object_name}")
        
        return {
            'success': True,
            'url': public_url,
            'filename': filename,
            'object_name': object_name,
            'size': file_size
        }
        
    except S3Error as e:
        error_msg = f"Error de MinIO: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Error al subir archivo: {str(e)}"
        logger.error(error_msg)
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