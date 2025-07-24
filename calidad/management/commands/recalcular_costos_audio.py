from django.core.management.base import BaseCommand
from calidad.models import UsoProcesamientoAudio
from decimal import Decimal

class Command(BaseCommand):
    help = 'Recalcula los costos de transcripción y análisis para todos los registros de UsoProcesamientoAudio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué registros se actualizarían sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Obtener todos los registros de UsoProcesamientoAudio
        registros = UsoProcesamientoAudio.objects.all()
        total_registros = registros.count()
        
        if total_registros == 0:
            self.stdout.write(
                self.style.WARNING('No se encontraron registros de UsoProcesamientoAudio')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Encontrados {total_registros} registros para procesar')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios reales')
            )
        
        registros_actualizados = 0
        costo_total_anterior = Decimal('0')
        costo_total_nuevo = Decimal('0')
        
        for registro in registros:
            # Calcular costo anterior
            costo_anterior = (registro.costo_transcripcion or Decimal('0')) + (registro.costo_analisis or Decimal('0'))
            costo_total_anterior += costo_anterior
            
            # Recalcular costos
            if registro.duracion_audio_segundos > 0:
                # Calcular costo de transcripción
                registro.calcular_costo_transcripcion()
                
                # Calcular costo de análisis si tiene tokens
                if hasattr(registro, 'tokens_analisis') and registro.tokens_analisis:
                    registro.calcular_costo_analisis()
                
                # Calcular nuevo costo total
                costo_nuevo = (registro.costo_transcripcion or Decimal('0')) + (registro.costo_analisis or Decimal('0'))
                costo_total_nuevo += costo_nuevo
                
                if not dry_run:
                    registro.save()
                
                registros_actualizados += 1
                
                self.stdout.write(
                    f'Registro {registro.id}: '
                    f'Duración: {registro.duracion_audio_segundos}s, '
                    f'Costo anterior: ${costo_anterior:.6f}, '
                    f'Costo nuevo: ${costo_nuevo:.6f}'
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Registro {registro.id}: Sin duración de audio, omitiendo'
                    )
                )
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Registros procesados: {registros_actualizados}/{total_registros}'
            )
        )
        self.stdout.write(
            f'Costo total anterior: ${costo_total_anterior:.6f}'
        )
        self.stdout.write(
            f'Costo total nuevo: ${costo_total_nuevo:.6f}'
        )
        self.stdout.write(
            f'Diferencia: ${costo_total_nuevo - costo_total_anterior:.6f}'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nPara aplicar los cambios, ejecuta el comando sin --dry-run'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n¡Costos recalculados exitosamente!'
                )
            )