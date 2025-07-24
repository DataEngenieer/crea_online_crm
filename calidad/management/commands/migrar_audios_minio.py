from django.core.management.base import BaseCommand
from django.db import transaction
from calidad.models import Speech
import logging

class Command(BaseCommand):
    help = 'Migra archivos de audio existentes a MinIO'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta una simulación sin realizar cambios reales',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la subida incluso si ya está marcado como subido',
        )
        parser.add_argument(
            '--speech-id',
            type=int,
            help='ID específico de Speech para migrar (opcional)',
        )
    
    def handle(self, *args, **options):
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        dry_run = options['dry_run']
        force = options['force']
        speech_id = options.get('speech_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se realizarán cambios reales')
            )
        
        # Filtrar registros de Speech
        queryset = Speech.objects.all()
        
        if speech_id:
            queryset = queryset.filter(id=speech_id)
            
        if not force:
            # Solo archivos que no han sido subidos a MinIO
            queryset = queryset.filter(subido_a_minio=False)
        
        # Filtrar solo los que tienen archivo de audio
        queryset = queryset.exclude(audio='')
        
        total_archivos = queryset.count()
        
        if total_archivos == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay archivos para migrar')
            )
            return
        
        self.stdout.write(
            f'Se encontraron {total_archivos} archivos para migrar'
        )
        
        exitosos = 0
        errores = 0
        
        for speech in queryset:
            try:
                self.stdout.write(
                    f'Procesando Speech ID {speech.id} - Auditoría {speech.auditoria.id}'
                )
                
                if not dry_run:
                    # Resetear estado si es forzado
                    if force:
                        speech.subido_a_minio = False
                        speech.minio_url = None
                        speech.minio_object_name = None
                    
                    # Intentar subir a MinIO
                    speech._subir_audio_a_minio()
                    
                    if speech.subido_a_minio:
                        # Guardar cambios
                        speech.save(update_fields=[
                            'minio_url', 
                            'minio_object_name', 
                            'subido_a_minio', 
                            'fecha_actualizacion'
                        ])
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Speech {speech.id} subido exitosamente: {speech.minio_url}'
                            )
                        )
                        exitosos += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Error al subir Speech {speech.id}'
                            )
                        )
                        errores += 1
                else:
                    # Modo simulación
                    self.stdout.write(
                        f'[SIMULACIÓN] Se subiría Speech {speech.id} con archivo: {speech.audio.name}'
                    )
                    exitosos += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error procesando Speech {speech.id}: {str(e)}'
                    )
                )
                errores += 1
                logger.error(f'Error en Speech {speech.id}: {str(e)}')
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE MIGRACIÓN')
        self.stdout.write('='*50)
        self.stdout.write(f'Total archivos procesados: {total_archivos}')
        self.stdout.write(
            self.style.SUCCESS(f'Exitosos: {exitosos}')
        )
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(f'Errores: {errores}')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nEjecuta sin --dry-run para realizar los cambios reales')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n¡Migración completada!')
            )