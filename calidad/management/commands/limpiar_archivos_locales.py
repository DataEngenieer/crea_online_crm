from django.core.management.base import BaseCommand
from calidad.models import Speech
import os
import logging

class Command(BaseCommand):
    help = 'Elimina archivos de audio locales que ya están subidos a MinIO'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la eliminación sin realizar cambios reales',
        )
        parser.add_argument(
            '--speech-id',
            type=int,
            help='ID específico del registro Speech a procesar',
        )
    
    def handle(self, *args, **options):
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        dry_run = options['dry_run']
        speech_id = options.get('speech_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO SIMULACIÓN - No se realizarán cambios reales'))
        
        # Filtrar registros
        if speech_id:
            speeches = Speech.objects.filter(id=speech_id)
            if not speeches.exists():
                self.stdout.write(self.style.ERROR(f'No se encontró Speech con ID {speech_id}'))
                return
        else:
            speeches = Speech.objects.filter(subido_a_minio=True)
        
        total_speeches = speeches.count()
        self.stdout.write(f'Procesando {total_speeches} registros Speech...')
        
        archivos_eliminados = 0
        archivos_no_encontrados = 0
        errores = 0
        
        for speech in speeches:
            try:
                # Verificar si el archivo local existe
                if speech.audio and hasattr(speech.audio, 'path'):
                    archivo_path = speech.audio.path
                    
                    if os.path.exists(archivo_path):
                        if dry_run:
                            self.stdout.write(f'[SIMULACIÓN] Eliminaría: {archivo_path}')
                            archivos_eliminados += 1
                        else:
                            # Eliminar archivo físico
                            os.remove(archivo_path)
                            
                            # Limpiar referencia del campo FileField
                            speech.audio = None
                            speech.save(update_fields=['audio'])
                            
                            self.stdout.write(f'Eliminado: {archivo_path}')
                            logger.info(f'Archivo local eliminado: {archivo_path}')
                            archivos_eliminados += 1
                    else:
                        self.stdout.write(f'Archivo no encontrado: {archivo_path}')
                        archivos_no_encontrados += 1
                        
                        if not dry_run:
                            # Limpiar referencia si el archivo no existe
                            speech.audio = None
                            speech.save(update_fields=['audio'])
                else:
                    self.stdout.write(f'Speech ID {speech.id}: No tiene archivo local')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error procesando Speech ID {speech.id}: {str(e)}')
                )
                logger.error(f'Error procesando Speech ID {speech.id}: {str(e)}')
                errores += 1
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE LA LIMPIEZA:')
        self.stdout.write(f'Total de registros procesados: {total_speeches}')
        self.stdout.write(f'Archivos eliminados: {archivos_eliminados}')
        self.stdout.write(f'Archivos no encontrados: {archivos_no_encontrados}')
        self.stdout.write(f'Errores: {errores}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nEjecuta sin --dry-run para realizar los cambios reales'))
        else:
            self.stdout.write(self.style.SUCCESS('\n¡Limpieza completada exitosamente!'))