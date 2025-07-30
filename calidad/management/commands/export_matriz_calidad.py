from django.core.management.base import BaseCommand
from django.core import serializers
from django.http import JsonResponse
import json
import os
from datetime import datetime
from calidad.models import MatrizCalidad

class Command(BaseCommand):
    help = 'Exporta todos los datos del modelo MatrizCalidad a un archivo JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='matriz_calidad_export.json',
            help='Nombre del archivo de salida (por defecto: matriz_calidad_export.json)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['django', 'custom'],
            default='custom',
            help='Formato de exportación: django (serializer nativo) o custom (formato personalizado)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        export_format = options['format']
        
        try:
            # Obtener todos los registros de MatrizCalidad
            matrices = MatrizCalidad.objects.all().select_related('usuario_creacion')
            
            if not matrices.exists():
                self.stdout.write(
                    self.style.WARNING('No se encontraron registros en MatrizCalidad para exportar')
                )
                return
            
            if export_format == 'django':
                # Usar el serializer nativo de Django
                data = serializers.serialize('json', matrices, indent=2)
                
                # Escribir directamente el JSON serializado
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(data)
            
            else:
                # Formato personalizado más legible
                export_data = {
                    'metadata': {
                        'export_date': datetime.now().isoformat(),
                        'total_records': matrices.count(),
                        'model': 'calidad.MatrizCalidad',
                        'version': '1.0'
                    },
                    'data': []
                }
                
                for matriz in matrices:
                    matriz_data = {
                        'id': matriz.id,
                        'tipologia': matriz.tipologia,
                        'categoria': matriz.categoria,
                        'indicador': matriz.indicador,
                        'ponderacion': float(matriz.ponderacion),
                        'activo': matriz.activo,
                        'usuario_creacion': {
                            'id': matriz.usuario_creacion.id,
                            'username': matriz.usuario_creacion.username,
                            'first_name': matriz.usuario_creacion.first_name,
                            'last_name': matriz.usuario_creacion.last_name,
                            'email': matriz.usuario_creacion.email
                        },
                        'fecha_creacion': matriz.fecha_creacion.isoformat(),
                        'fecha_actualizacion': matriz.fecha_actualizacion.isoformat()
                    }
                    export_data['data'].append(matriz_data)
                
                # Escribir el JSON con formato personalizado
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Obtener el tamaño del archivo
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n=== Exportación completada exitosamente ===\n'
                    f'Archivo: {output_file}\n'
                    f'Registros exportados: {matrices.count()}\n'
                    f'Formato: {export_format}\n'
                    f'Tamaño del archivo: {file_size_mb:.2f} MB\n'
                    f'Fecha de exportación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                )
            )
            
            # Mostrar resumen por tipología
            self.stdout.write('\n=== Resumen por Tipología ===')
            tipologias = matrices.values('tipologia').distinct()
            for tip in tipologias:
                count = matrices.filter(tipologia=tip['tipologia']).count()
                self.stdout.write(f'{tip["tipologia"]}: {count} registros')
            
            # Mostrar resumen por estado activo
            activos = matrices.filter(activo=True).count()
            inactivos = matrices.filter(activo=False).count()
            self.stdout.write('\n=== Resumen por Estado ===')
            self.stdout.write(f'Activos: {activos} registros')
            self.stdout.write(f'Inactivos: {inactivos} registros')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la exportación: {str(e)}')
            )
            raise e