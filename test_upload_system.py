#!/usr/bin/env python
"""
Script de prueba final para verificar que el sistema de subida a MinIO funciona correctamente
con las mejoras aplicadas
"""

import os
import sys
import django
import tempfile
import time
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from calidad.models import Speech, Auditoria
from calidad.utils.minio_utils import subir_a_minio, get_minio_client
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def crear_archivo_audio_prueba():
    """Crea un archivo de audio de prueba"""
    print("\n=== CREANDO ARCHIVO DE AUDIO DE PRUEBA ===")
    
    # Crear un archivo MP3 de prueba simple
    audio_content = b'\xff\xfb\x90\x00' + b'\x00' * 1000  # Header MP3 básico + datos
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    temp_file.write(audio_content)
    temp_file.close()
    
    print(f"Archivo de prueba creado: {temp_file.name}")
    print(f"Tamaño: {len(audio_content)} bytes")
    
    return temp_file.name

def probar_subida_directa_minio():
    """Prueba la subida directa a MinIO"""
    print("\n=== PRUEBA DE SUBIDA DIRECTA A MINIO ===")
    
    archivo_prueba = crear_archivo_audio_prueba()
    
    try:
        # Probar subida directa
        resultado = subir_a_minio(archivo_prueba, 'test_direct_upload.mp3')
        
        if resultado['exito']:
            print(f"✅ Subida directa exitosa")
            print(f"   URL: {resultado['url']}")
            print(f"   Object Name: {resultado['object_name']}")
            return True
        else:
            print(f"❌ Error en subida directa: {resultado['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en subida directa: {e}")
        return False
    finally:
        # Limpiar archivo de prueba
        try:
            os.unlink(archivo_prueba)
            print(f"🧹 Archivo de prueba eliminado")
        except Exception as e:
            print(f"⚠️ Error al eliminar archivo de prueba: {e}")

def probar_creacion_speech():
    """Prueba la creación de un Speech con archivo"""
    print("\n=== PRUEBA DE CREACIÓN DE SPEECH ===")
    
    archivo_prueba = crear_archivo_audio_prueba()
    
    try:
        # Crear una auditoría de prueba
        from django.contrib.auth.models import User
        
        # Buscar un usuario existente o crear uno de prueba
        try:
            usuario = User.objects.filter(is_staff=True).first()
            if not usuario:
                usuario = User.objects.create_user(
                    username='test_user',
                    email='test@test.com',
                    password='testpass123'
                )
        except Exception as e:
            print(f"⚠️ Error al obtener/crear usuario: {e}")
            return False
        
        # Crear auditoría de prueba
        auditoria = Auditoria.objects.create(
            numero_llamada='TEST-UPLOAD-' + str(int(time.time())),
            agente=usuario,
            auditor=usuario,
            fecha_llamada=timezone.now().date(),
            observaciones='Prueba de subida con mejoras'
        )
        
        print(f"Auditoría de prueba creada: ID {auditoria.id}")
        
        # Crear archivo Django
        with open(archivo_prueba, 'rb') as f:
            django_file = SimpleUploadedFile(
                name='test_speech_upload.mp3',
                content=f.read(),
                content_type='audio/mpeg'
            )
        
        # Crear Speech
        speech = Speech.objects.create(
            auditoria=auditoria,
            audio=django_file
        )
        
        print(f"Speech creado: ID {speech.id}")
        print(f"Archivo local: {speech.audio.path if speech.audio else 'None'}")
        
        # Esperar un momento para que se procese
        time.sleep(2)
        
        # Verificar estado
        speech.refresh_from_db()
        
        print(f"Estado después de creación:")
        print(f"  - Subido a MinIO: {speech.subido_a_minio}")
        print(f"  - URL MinIO: {speech.minio_url}")
        print(f"  - Object Name: {speech.minio_object_name}")
        print(f"  - Archivo local existe: {speech.audio and hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path)}")
        
        # Verificar que se puede acceder a la URL de audio
        audio_url = speech.get_audio_url()
        if audio_url:
            print(f"✅ URL de audio disponible: {audio_url}")
            return True
        else:
            print(f"❌ No se pudo obtener URL de audio")
            return False
            
    except Exception as e:
        print(f"❌ Error en creación de Speech: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpiar archivo de prueba
        try:
            os.unlink(archivo_prueba)
            print(f"🧹 Archivo de prueba eliminado")
        except Exception as e:
            print(f"⚠️ Error al eliminar archivo de prueba: {e}")

def verificar_estado_sistema():
    """Verifica el estado general del sistema"""
    print("\n=== VERIFICACIÓN DEL ESTADO DEL SISTEMA ===")
    
    # Verificar configuración MinIO
    try:
        client = get_minio_client()
        print(f"✅ Cliente MinIO creado correctamente")
        
        # Verificar bucket
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get('MINIO_BUCKET_NAME_LLAMADAS', 'default-bucket')
        
        if client.bucket_exists(bucket_name):
            print(f"✅ Bucket '{bucket_name}' existe")
        else:
            print(f"❌ Bucket '{bucket_name}' no existe")
            return False
            
    except Exception as e:
        print(f"❌ Error en configuración MinIO: {e}")
        return False
    
    # Verificar estadísticas de Speech
    total_speeches = Speech.objects.count()
    subidos_minio = Speech.objects.filter(subido_a_minio=True).count()
    con_archivo_local = 0
    
    for speech in Speech.objects.all():
        if speech.audio and hasattr(speech.audio, 'path'):
            try:
                if os.path.exists(speech.audio.path):
                    con_archivo_local += 1
            except:
                pass
    
    print(f"📊 Estadísticas Speech:")
    print(f"  - Total: {total_speeches}")
    print(f"  - Subidos a MinIO: {subidos_minio}")
    print(f"  - Con archivo local: {con_archivo_local}")
    
    return True

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 PRUEBAS DEL SISTEMA DE SUBIDA MEJORADO")
    print("=" * 50)
    
    pruebas_exitosas = 0
    total_pruebas = 3
    
    # 1. Verificar estado del sistema
    if verificar_estado_sistema():
        pruebas_exitosas += 1
        print("✅ Verificación del sistema: EXITOSA")
    else:
        print("❌ Verificación del sistema: FALLIDA")
    
    # 2. Probar subida directa a MinIO
    if probar_subida_directa_minio():
        pruebas_exitosas += 1
        print("✅ Subida directa a MinIO: EXITOSA")
    else:
        print("❌ Subida directa a MinIO: FALLIDA")
    
    # 3. Probar creación de Speech
    if probar_creacion_speech():
        pruebas_exitosas += 1
        print("✅ Creación de Speech: EXITOSA")
    else:
        print("❌ Creación de Speech: FALLIDA")
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    print(f"Pruebas exitosas: {pruebas_exitosas}/{total_pruebas}")
    
    if pruebas_exitosas == total_pruebas:
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        print("   El sistema de subida a MinIO está funcionando correctamente")
        print("   Las mejoras han resuelto el problema de archivos bloqueados")
    elif pruebas_exitosas > 0:
        print(f"\n⚠️ PRUEBAS PARCIALMENTE EXITOSAS ({pruebas_exitosas}/{total_pruebas})")
        print("   Algunas funcionalidades están trabajando, pero hay problemas pendientes")
    else:
        print("\n❌ TODAS LAS PRUEBAS FALLARON")
        print("   Hay problemas serios que necesitan atención")
    
    print("\n💡 PRÓXIMOS PASOS:")
    if pruebas_exitosas == total_pruebas:
        print("   1. El sistema está listo para uso en producción")
        print("   2. Los archivos se suben correctamente a MinIO")
        print("   3. No hay más problemas de archivos bloqueados")
    else:
        print("   1. Revisar los errores mostrados arriba")
        print("   2. Verificar la configuración de MinIO")
        print("   3. Comprobar permisos de archivos")

if __name__ == "__main__":
    from django.utils import timezone
    main()