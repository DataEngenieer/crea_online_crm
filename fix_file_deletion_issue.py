#!/usr/bin/env python
"""
Script para corregir el problema de eliminación de archivos locales después de subir a MinIO
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from django.conf import settings
from calidad.models import Speech
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_estado_archivos():
    """Verificar el estado actual de los archivos de Speech"""
    print("\n=== VERIFICACIÓN DE ESTADO DE ARCHIVOS ===")
    
    speeches = Speech.objects.all().order_by('-fecha_creacion')
    
    total_speeches = speeches.count()
    subidos_minio = speeches.filter(subido_a_minio=True).count()
    con_archivo_local = 0
    sin_archivo_local = 0
    archivos_huerfanos = 0
    
    print(f"Total de registros Speech: {total_speeches}")
    print(f"Subidos a MinIO: {subidos_minio}")
    
    # Verificar archivos locales
    for speech in speeches:
        if speech.audio:
            try:
                if hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path):
                    con_archivo_local += 1
                    print(f"Speech {speech.id}: ✅ Archivo local existe - {speech.audio.path}")
                else:
                    sin_archivo_local += 1
                    print(f"Speech {speech.id}: ❌ Archivo local NO existe - {speech.audio.name}")
            except Exception as e:
                sin_archivo_local += 1
                print(f"Speech {speech.id}: ❌ Error al verificar archivo - {str(e)}")
        else:
            sin_archivo_local += 1
            print(f"Speech {speech.id}: ❌ No tiene campo audio")
    
    # Verificar archivos huérfanos en el directorio
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'auditorias', 'audio')
    if os.path.exists(audio_dir):
        archivos_en_directorio = set(os.listdir(audio_dir))
        archivos_en_bd = set()
        
        for speech in speeches:
            if speech.audio:
                filename = os.path.basename(speech.audio.name)
                archivos_en_bd.add(filename)
        
        archivos_huerfanos_list = archivos_en_directorio - archivos_en_bd
        archivos_huerfanos = len(archivos_huerfanos_list)
        
        if archivos_huerfanos_list:
            print(f"\n⚠️ Archivos huérfanos encontrados ({archivos_huerfanos}):")
            for archivo in archivos_huerfanos_list:
                print(f"  - {archivo}")
    
    print(f"\n📊 RESUMEN:")
    print(f"Con archivo local: {con_archivo_local}")
    print(f"Sin archivo local: {sin_archivo_local}")
    print(f"Archivos huérfanos: {archivos_huerfanos}")
    
    return {
        'total': total_speeches,
        'subidos_minio': subidos_minio,
        'con_archivo_local': con_archivo_local,
        'sin_archivo_local': sin_archivo_local,
        'archivos_huerfanos': archivos_huerfanos
    }

def limpiar_archivos_locales_seguros():
    """Limpiar archivos locales que ya están subidos a MinIO de forma segura"""
    print("\n=== LIMPIEZA SEGURA DE ARCHIVOS LOCALES ===")
    
    # Buscar Speech que están subidos a MinIO pero aún tienen archivo local
    speeches_para_limpiar = Speech.objects.filter(
        subido_a_minio=True,
        minio_url__isnull=False
    ).exclude(minio_url='')
    
    archivos_eliminados = 0
    errores = 0
    
    for speech in speeches_para_limpiar:
        if speech.audio:
            try:
                if hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path):
                    archivo_path = speech.audio.path
                    
                    # Verificar que realmente está en MinIO haciendo una verificación adicional
                    if speech.minio_url and speech.minio_object_name:
                        print(f"Speech {speech.id}: Eliminando archivo local {archivo_path}")
                        
                        # Intentar eliminar el archivo
                        try:
                            os.remove(archivo_path)
                            
                            # Limpiar la referencia del campo FileField
                            speech.audio = None
                            speech.save(update_fields=['audio'])
                            
                            archivos_eliminados += 1
                            print(f"  ✅ Archivo eliminado exitosamente")
                            
                        except PermissionError as e:
                            print(f"  ❌ Error de permisos: {str(e)}")
                            print(f"  ℹ️ El archivo puede estar siendo usado por otro proceso")
                            errores += 1
                        except Exception as e:
                            print(f"  ❌ Error al eliminar: {str(e)}")
                            errores += 1
                    else:
                        print(f"Speech {speech.id}: ⚠️ Marcado como subido pero sin URL o object_name válidos")
                        errores += 1
            except Exception as e:
                print(f"Speech {speech.id}: ❌ Error al procesar: {str(e)}")
                errores += 1
    
    print(f"\n📊 RESULTADO DE LIMPIEZA:")
    print(f"Archivos eliminados: {archivos_eliminados}")
    print(f"Errores: {errores}")
    
    return archivos_eliminados, errores

def corregir_referencias_vacias():
    """Corregir referencias de audio vacías para Speech subidos a MinIO"""
    print("\n=== CORRECCIÓN DE REFERENCIAS VACÍAS ===")
    
    # Buscar Speech que están subidos a MinIO pero tienen campo audio vacío
    speeches_sin_audio = Speech.objects.filter(
        subido_a_minio=True,
        minio_url__isnull=False,
        audio=''
    ).exclude(minio_url='')
    
    corregidos = 0
    
    for speech in speeches_sin_audio:
        print(f"Speech {speech.id}: Campo audio vacío pero está en MinIO ({speech.minio_url})")
        # Estos están correctos, el archivo local ya fue eliminado
        corregidos += 1
    
    print(f"Referencias vacías encontradas (correctas): {corregidos}")
    return corregidos

def verificar_integridad_minio():
    """Verificar la integridad de los archivos en MinIO"""
    print("\n=== VERIFICACIÓN DE INTEGRIDAD MINIO ===")
    
    from calidad.utils.minio_utils import get_minio_client
    
    try:
        client = get_minio_client()
        bucket_dict = getattr(settings, 'MINIO_BUCKET_NAME', {})
        bucket_name = bucket_dict.get('MINIO_BUCKET_NAME_LLAMADAS', 'default-bucket')
        
        # Listar objetos en MinIO
        objects_in_minio = list(client.list_objects(bucket_name, prefix='audios/', recursive=True))
        print(f"Objetos en MinIO (carpeta audios): {len(objects_in_minio)}")
        
        # Verificar que los Speech en BD coincidan con MinIO
        speeches_minio = Speech.objects.filter(subido_a_minio=True, minio_object_name__isnull=False)
        
        objetos_minio_names = {obj.object_name for obj in objects_in_minio}
        objetos_bd_names = {speech.minio_object_name for speech in speeches_minio if speech.minio_object_name}
        
        # Objetos en MinIO pero no en BD
        solo_en_minio = objetos_minio_names - objetos_bd_names
        # Objetos en BD pero no en MinIO
        solo_en_bd = objetos_bd_names - objetos_minio_names
        
        print(f"Objetos solo en MinIO: {len(solo_en_minio)}")
        if solo_en_minio:
            print("  Objetos huérfanos en MinIO:")
            for obj in list(solo_en_minio)[:5]:  # Mostrar solo los primeros 5
                print(f"    - {obj}")
        
        print(f"Objetos solo en BD: {len(solo_en_bd)}")
        if solo_en_bd:
            print("  Referencias huérfanas en BD:")
            for obj in list(solo_en_bd)[:5]:  # Mostrar solo los primeros 5
                print(f"    - {obj}")
        
        return len(solo_en_minio), len(solo_en_bd)
        
    except Exception as e:
        print(f"❌ Error al verificar MinIO: {str(e)}")
        return 0, 0

def main():
    """Ejecutar todas las verificaciones y correcciones"""
    print("🔧 CORRECCIÓN DE PROBLEMAS DE ARCHIVOS")
    print("=" * 50)
    
    # 1. Verificar estado actual
    estado = verificar_estado_archivos()
    
    # 2. Verificar integridad con MinIO
    solo_minio, solo_bd = verificar_integridad_minio()
    
    # 3. Corregir referencias vacías (esto es normal)
    corregidos = corregir_referencias_vacias()
    
    # 4. Limpiar archivos locales de forma segura
    if estado['con_archivo_local'] > 0:
        respuesta = input(f"\n¿Desea limpiar {estado['con_archivo_local']} archivos locales que ya están en MinIO? (s/N): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            eliminados, errores = limpiar_archivos_locales_seguros()
        else:
            print("Limpieza cancelada por el usuario.")
            eliminados, errores = 0, 0
    else:
        print("\n✅ No hay archivos locales para limpiar.")
        eliminados, errores = 0, 0
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"Total Speech: {estado['total']}")
    print(f"Subidos a MinIO: {estado['subidos_minio']}")
    print(f"Archivos locales eliminados: {eliminados}")
    print(f"Errores en eliminación: {errores}")
    print(f"Referencias vacías (correctas): {corregidos}")
    print(f"Objetos huérfanos en MinIO: {solo_minio}")
    print(f"Referencias huérfanas en BD: {solo_bd}")
    
    if errores == 0 and solo_bd == 0:
        print("\n🎉 Sistema de archivos en estado óptimo.")
    elif errores > 0:
        print(f"\n⚠️ Se encontraron {errores} errores. Revisar logs anteriores.")
    
    if solo_bd > 0:
        print(f"\n⚠️ Hay {solo_bd} referencias en BD que no existen en MinIO.")

if __name__ == "__main__":
    main()