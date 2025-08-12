from django.core.management.base import BaseCommand
from django.db import transaction
from telefonica.models import VentaPortabilidad
import logging

class Command(BaseCommand):
    help = 'Migra archivos confronta existentes a MinIO'
    
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
            '--venta-id',
            type=int,
            help='ID específico de VentaPortabilidad para migrar (opcional)',
        )
    
    def handle(self, *args, **options):
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        dry_run = options['dry_run']
        force = options['force']
        venta_id = options.get('venta_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se realizarán cambios reales')
            )
        
        # Filtrar registros de VentaPortabilidad
        queryset = VentaPortabilidad.objects.all()
        
        if venta_id:
            queryset = queryset.filter(id=venta_id)
            
        if not force:
            # Solo archivos que no han sido subidos a MinIO
            queryset = queryset.filter(confronta_subido_a_minio=False)
        
        # Filtrar solo los que tienen archivo confronta
        queryset = queryset.exclude(confronta='')
        
        total_archivos = queryset.count()
        
        if total_archivos == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay archivos confronta para migrar')
            )
            return
        
        self.stdout.write(
            f'Se encontraron {total_archivos} archivos confronta para migrar'
        )
        
        exitosos = 0
        errores = 0
        
        for venta in queryset:
            try:
                self.stdout.write(
                    f'Procesando Venta ID {venta.id} - Cliente: {venta.nombre_completo}'
                )
                
                if not dry_run:
                    # Resetear estado si es forzado
                    if force:
                        venta.confronta_subido_a_minio = False
                        venta.confronta_minio_url = None
                        venta.confronta_minio_object_name = None
                        venta.confronta_fecha_subida_minio = None
                    
                    # Intentar subir a MinIO
                    exito = venta._subir_confronta_a_minio()
                    
                    if exito and venta.confronta_subido_a_minio:
                        # Guardar cambios
                        venta.save(update_fields=[
                            'confronta_minio_url', 
                            'confronta_minio_object_name', 
                            'confronta_subido_a_minio', 
                            'confronta_fecha_subida_minio'
                        ])
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Venta {venta.id} - Confronta subida exitosamente: {venta.confronta_minio_url}'
                            )
                        )
                        exitosos += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Error al subir confronta de Venta {venta.id}'
                            )
                        )
                        errores += 1
                else:
                    # Modo simulación
                    self.stdout.write(
                        f'[SIMULACIÓN] Se subiría confronta de Venta {venta.id} con archivo: {venta.confronta.name}'
                    )
                    exitosos += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error procesando Venta {venta.id}: {str(e)}'
                    )
                )
                errores += 1
                logger.error(f'Error en Venta {venta.id}: {str(e)}')
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE MIGRACIÓN DE CONFRONTAS')
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
                self.style.SUCCESS('\n¡Migración de confrontas completada!')
            )
            
        # Estadísticas adicionales
        total_ventas = VentaPortabilidad.objects.count()
        ventas_con_confronta = VentaPortabilidad.objects.exclude(confronta='').count()
        ventas_en_minio = VentaPortabilidad.objects.filter(confronta_subido_a_minio=True).count()
        
        self.stdout.write('\n' + '-'*50)
        self.stdout.write('ESTADÍSTICAS GENERALES')
        self.stdout.write('-'*50)
        self.stdout.write(f'Total ventas: {total_ventas}')
        self.stdout.write(f'Ventas con confronta: {ventas_con_confronta}')
        self.stdout.write(f'Confrontas en MinIO: {ventas_en_minio}')
        
        if ventas_con_confronta > 0:
            porcentaje_minio = (ventas_en_minio / ventas_con_confronta) * 100
            self.stdout.write(f'Porcentaje migrado: {porcentaje_minio:.1f}%')