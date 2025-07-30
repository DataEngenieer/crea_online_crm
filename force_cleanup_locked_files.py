#!/usr/bin/env python
"""
Script para forzar la limpieza de archivos bloqueados después de las mejoras
"""

import os
import sys
import django
import time
import psutil
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

def encontrar_procesos_usando_archivo(file_path):
    """Encuentra procesos que están usando un archivo específico"""
    procesos = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                if proc.info['open_files']:
                    for file_info in proc.info['open_files']:
                        if file_info.path == file_path:
                            procesos.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'path': file_info.path
                            })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"Error al buscar procesos: {e}")
    
    return procesos

def intentar_eliminar_archivo_forzado(file_path, max_intentos=5):
    """Intenta eliminar un archivo con múltiples estrategias"""
    print(f"\n🔧 Intentando eliminar archivo bloqueado: {file_path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        print(f"  ✅ El archivo ya no existe")
        return True
    
    # Buscar procesos que usan el archivo
    procesos = encontrar_procesos_usando_archivo(file_path)
    if procesos:
        print(f"  ⚠️ Archivo en uso por {len(procesos)} proceso(s):")
        for proc in procesos:
            print(f"    - PID {proc['pid']}: {proc['name']}")
    
    # Intentar eliminar con diferentes estrategias
    for intento in range(max_intentos):
        try:
            # Estrategia 1: Eliminación directa
            os.remove(file_path)
            print(f"  ✅ Archivo eliminado exitosamente (intento {intento + 1})")
            return True
            
        except PermissionError:
            print(f"  ❌ Intento {intento + 1}: Archivo en uso")
            
            if intento < max_intentos - 1:
                # Esperar un poco antes del siguiente intento
                tiempo_espera = 2 ** intento  # Espera exponencial
                print(f"  ⏳ Esperando {tiempo_espera} segundos...")
                time.sleep(tiempo_espera)
                
                # Verificar si los procesos siguen activos
                procesos_actuales = encontrar_procesos_usando_archivo(file_path)
                if len(procesos_actuales) < len(procesos):
                    print(f"  📉 Menos procesos usando el archivo ({len(procesos_actuales)} vs {len(procesos)})")
                    procesos = procesos_actuales
            
        except Exception as e:
            print(f"  ❌ Error inesperado en intento {intento + 1}: {e}")
            if intento < max_intentos - 1:
                time.sleep(1)
    
    print(f"  ❌ No se pudo eliminar el archivo después de {max_intentos} intentos")
    return False

def limpiar_archivos_bloqueados():
    """Limpia archivos que están bloqueados usando técnicas avanzadas"""
    print("\n=== LIMPIEZA FORZADA DE ARCHIVOS BLOQUEADOS ===")
    
    # Buscar Speech que están subidos a MinIO pero aún tienen archivo local
    speeches_para_limpiar = Speech.objects.filter(
        subido_a_minio=True,
        minio_url__isnull=False
    ).exclude(minio_url='')
    
    archivos_eliminados = 0
    archivos_bloqueados = 0
    
    for speech in speeches_para_limpiar:
        if speech.audio:
            try:
                if hasattr(speech.audio, 'path') and os.path.exists(speech.audio.path):
                    archivo_path = speech.audio.path
                    
                    # Verificar que realmente está en MinIO
                    if speech.minio_url and speech.minio_object_name:
                        print(f"\nSpeech {speech.id}: Procesando archivo {archivo_path}")
                        
                        # Intentar eliminación forzada
                        if intentar_eliminar_archivo_forzado(archivo_path):
                            # Limpiar la referencia del campo FileField
                            speech.audio = None
                            speech.save(update_fields=['audio'])
                            archivos_eliminados += 1
                        else:
                            archivos_bloqueados += 1
                            
                            # Marcar para limpieza manual posterior
                            print(f"  📝 Archivo marcado para limpieza manual")
                    else:
                        print(f"Speech {speech.id}: ⚠️ Marcado como subido pero sin URL o object_name válidos")
            except Exception as e:
                print(f"Speech {speech.id}: ❌ Error al procesar: {str(e)}")
                archivos_bloqueados += 1
    
    print(f"\n📊 RESULTADO DE LIMPIEZA FORZADA:")
    print(f"Archivos eliminados: {archivos_eliminados}")
    print(f"Archivos aún bloqueados: {archivos_bloqueados}")
    
    return archivos_eliminados, archivos_bloqueados

def limpiar_archivos_temporales():
    """Limpia archivos temporales que puedan haber quedado"""
    print("\n=== LIMPIEZA DE ARCHIVOS TEMPORALES ===")
    
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    archivos_temp_eliminados = 0
    
    # Buscar archivos temporales de audio
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.startswith('temp_audio_') and file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                try:
                    # Verificar si el archivo es antiguo (más de 1 hora)
                    import time
                    file_age = time.time() - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hora
                        if intentar_eliminar_archivo_forzado(file_path, max_intentos=2):
                            archivos_temp_eliminados += 1
                            print(f"  ✅ Archivo temporal eliminado: {file}")
                except Exception as e:
                    print(f"  ❌ Error al procesar archivo temporal {file}: {e}")
    
    print(f"Archivos temporales eliminados: {archivos_temp_eliminados}")
    return archivos_temp_eliminados

def verificar_mejoras():
    """Verifica que las mejoras estén funcionando"""
    print("\n=== VERIFICACIÓN DE MEJORAS ===")
    
    # Verificar que el código actualizado esté en su lugar
    views_path = os.path.join(settings.BASE_DIR, 'calidad', 'views.py')
    whixperx_path = os.path.join(settings.BASE_DIR, 'calidad', 'utils', 'whixperx.py')
    
    mejoras_aplicadas = 0
    
    # Verificar views.py
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'temp_dir=None' in content and 'shutil.copy2' in content:
                print("  ✅ Mejoras en views.py aplicadas correctamente")
                mejoras_aplicadas += 1
            else:
                print("  ❌ Mejoras en views.py NO encontradas")
    except Exception as e:
        print(f"  ❌ Error al verificar views.py: {e}")
    
    # Verificar whixperx.py
    try:
        with open(whixperx_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'file_content = f.read()' in content:
                print("  ✅ Mejoras en whixperx.py aplicadas correctamente")
                mejoras_aplicadas += 1
            else:
                print("  ❌ Mejoras en whixperx.py NO encontradas")
    except Exception as e:
        print(f"  ❌ Error al verificar whixperx.py: {e}")
    
    print(f"\nMejoras aplicadas: {mejoras_aplicadas}/2")
    return mejoras_aplicadas == 2

def main():
    """Ejecutar limpieza forzada y verificaciones"""
    print("🔧 LIMPIEZA FORZADA DE ARCHIVOS BLOQUEADOS")
    print("=" * 50)
    
    # 1. Verificar que las mejoras estén aplicadas
    if not verificar_mejoras():
        print("\n⚠️ ADVERTENCIA: No todas las mejoras están aplicadas")
        print("   Las nuevas subidas pueden seguir teniendo problemas")
    
    # 2. Limpiar archivos temporales
    temp_eliminados = limpiar_archivos_temporales()
    
    # 3. Limpiar archivos bloqueados
    eliminados, bloqueados = limpiar_archivos_bloqueados()
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"Archivos eliminados: {eliminados}")
    print(f"Archivos temporales eliminados: {temp_eliminados}")
    print(f"Archivos aún bloqueados: {bloqueados}")
    
    if bloqueados == 0:
        print("\n🎉 Todos los archivos han sido limpiados exitosamente.")
        print("   Las nuevas subidas deberían funcionar sin problemas.")
    else:
        print(f"\n⚠️ Quedan {bloqueados} archivos bloqueados.")
        print("   Puede ser necesario reiniciar el servidor o cerrar aplicaciones que usen los archivos.")
    
    print("\n💡 RECOMENDACIONES:")
    print("   1. Las mejoras aplicadas deberían prevenir futuros bloqueos")
    print("   2. Los archivos ahora se procesan usando copias temporales")
    print("   3. El manejo de archivos en whixperx.py ha sido mejorado")
    print("   4. Prueba subir un nuevo archivo de audio para verificar")

if __name__ == "__main__":
    main()