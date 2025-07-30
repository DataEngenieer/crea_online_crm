#!/usr/bin/env python
"""
Script de diagnóstico para probar la subida a MinIO paso a paso
"""

import os
import sys
import django
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from django.conf import settings
from calidad.utils.minio_utils import get_minio_client, subir_a_minio
from calidad.models import Speech, Auditoria
from django.contrib.auth import get_user_model
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minio_configuration():
    """Probar la configuración de MinIO"""
    print("\n=== PRUEBA 1: Configuración de MinIO ===")
    
    # Verificar variables de entorno
    endpoint = getattr(settings, 'MINIO_ENDPOINT', '')
    access_key = getattr(settings, 'MINIO_ACCESS_KEY', '')
    secret_key = getattr(settings, 'MINIO_SECRET_KEY', '')
    bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
    
    print(f"MINIO_ENDPOINT: {endpoint}")
    print(f"MINIO_ACCESS_KEY: {access_key[:10]}..." if access_key else "MINIO_ACCESS_KEY: NO_CONFIGURADO")
    print(f"MINIO_SECRET_KEY: {'*' * 10}..." if secret_key else "MINIO_SECRET_KEY: NO_CONFIGURADO")
    print(f"MINIO_BUCKET_NAME: {bucket_dict}")
    
    if not all([endpoint, access_key, secret_key]):
        print("❌ ERROR: Faltan variables de configuración de MinIO")
        return False
    
    print("✅ Configuración de MinIO completa")
    return True

def test_minio_client():
    """Probar la creación del cliente MinIO"""
    print("\n=== PRUEBA 2: Cliente MinIO ===")
    
    try:
        client = get_minio_client()
        print("✅ Cliente MinIO creado exitosamente")
        return client
    except Exception as e:
        print(f"❌ ERROR al crear cliente MinIO: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def test_bucket_access(client):
    """Probar el acceso al bucket"""
    print("\n=== PRUEBA 3: Acceso al bucket ===")
    
    if not client:
        print("❌ No hay cliente MinIO disponible")
        return False
    
    try:
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get('MINIO_BUCKET_NAME_LLAMADAS', 'default-bucket')
        
        print(f"Verificando bucket: {bucket_name}")
        
        # Verificar si el bucket existe
        if client.bucket_exists(bucket_name):
            print(f"✅ Bucket '{bucket_name}' existe")
        else:
            print(f"⚠️ Bucket '{bucket_name}' no existe, intentando crearlo...")
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' creado exitosamente")
        
        # Listar objetos en el bucket (solo los primeros 5)
        objects = list(client.list_objects(bucket_name, recursive=True))
        print(f"Objetos en el bucket: {len(objects)}")
        if objects:
            print("Primeros 5 objetos:")
            for obj in objects[:5]:
                print(f"  - {obj.object_name} ({obj.size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR al acceder al bucket: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_file_upload():
    """Probar la subida de un archivo de prueba"""
    print("\n=== PRUEBA 4: Subida de archivo de prueba ===")
    
    try:
        # Crear un archivo de prueba
        test_content = b"Este es un archivo de prueba para MinIO"
        test_file = SimpleUploadedFile(
            "test_debug_minio.txt",
            test_content,
            content_type="text/plain"
        )
        
        print(f"Archivo de prueba creado: {test_file.name} ({len(test_content)} bytes)")
        
        # Intentar subir el archivo
        resultado = subir_a_minio(
            archivo=test_file,
            nombre_personalizado="debug_test_file",
            carpeta="debug",
            bucket_type="MINIO_BUCKET_NAME_LLAMADAS"
        )
        
        print(f"Resultado de la subida: {resultado}")
        
        if resultado['success']:
            print(f"✅ Archivo subido exitosamente")
            print(f"URL: {resultado['url']}")
            print(f"Object name: {resultado['object_name']}")
            return True
        else:
            print(f"❌ ERROR en la subida: {resultado.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR al probar subida: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_speech_model():
    """Probar la creación de un Speech con archivo"""
    print("\n=== PRUEBA 5: Modelo Speech ===")
    
    try:
        User = get_user_model()
        
        # Buscar un usuario existente o crear uno de prueba
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
            if not user:
                print("❌ No hay usuarios disponibles para la prueba")
                return False
        except Exception as e:
            print(f"❌ Error al obtener usuario: {str(e)}")
            return False
        
        print(f"Usuario para prueba: {user.username}")
        
        # Crear una auditoría de prueba
        auditoria = Auditoria.objects.create(
            agente=user,
            numero_telefono="1234567890",
            evaluador=user,
            tipo_monitoreo="speech",
            observaciones="Auditoría de prueba para debug MinIO"
        )
        
        print(f"Auditoría creada: ID {auditoria.id}")
        
        # Crear archivo de prueba
        test_content = b"Contenido de audio de prueba para Speech"
        test_file = SimpleUploadedFile(
            "test_speech_audio.mp3",
            test_content,
            content_type="audio/mpeg"
        )
        
        # Crear Speech
        speech = Speech.objects.create(
            auditoria=auditoria,
            audio=test_file
        )
        
        print(f"Speech creado: ID {speech.id}")
        print(f"Archivo de audio: {speech.audio.name}")
        print(f"Subido a MinIO: {speech.subido_a_minio}")
        print(f"URL de MinIO: {speech.minio_url}")
        
        if speech.subido_a_minio and speech.minio_url:
            print("✅ Speech creado y subido a MinIO exitosamente")
            return True
        else:
            print("❌ Speech creado pero no se subió a MinIO")
            return False
            
    except Exception as e:
        print(f"❌ ERROR al probar Speech: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🔍 DIAGNÓSTICO DE SUBIDA A MINIO")
    print("=" * 50)
    
    # Ejecutar pruebas en secuencia
    tests = [
        ("Configuración", test_minio_configuration),
        ("Cliente MinIO", test_minio_client),
        ("Acceso al bucket", lambda: test_bucket_access(test_minio_client())),
        ("Subida de archivo", test_file_upload),
        ("Modelo Speech", test_speech_model)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if not result:
                print(f"\n⚠️ La prueba '{test_name}' falló. Continuando con las siguientes...")
        except Exception as e:
            print(f"\n❌ Error en la prueba '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 Todas las pruebas pasaron. MinIO debería estar funcionando correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar los errores anteriores.")

if __name__ == "__main__":
    main()