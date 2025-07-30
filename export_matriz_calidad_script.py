#!/usr/bin/env python
"""
Script para exportar datos del modelo MatrizCalidad a JSON
Ejecución: python export_matriz_calidad_script.py
"""

import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crea_online_crm.settings')
django.setup()

from calidad.models import MatrizCalidad

def export_matriz_calidad_to_json(output_file='matriz_calidad_export.json'):
    """
    Exporta todos los datos del modelo MatrizCalidad a un archivo JSON
    
    Args:
        output_file (str): Nombre del archivo de salida
    
    Returns:
        dict: Información sobre la exportación
    """
    try:
        print("Iniciando exportación de MatrizCalidad...")
        
        # Obtener todos los registros de MatrizCalidad
        matrices = MatrizCalidad.objects.all().select_related('usuario_creacion')
        
        if not matrices.exists():
            print("⚠️  No se encontraron registros en MatrizCalidad para exportar")
            return {'success': False, 'message': 'No hay datos para exportar'}
        
        # Preparar datos para exportación
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_records': matrices.count(),
                'model': 'calidad.MatrizCalidad',
                'version': '1.0',
                'script': 'export_matriz_calidad_script.py'
            },
            'data': []
        }
        
        print(f"Procesando {matrices.count()} registros...")
        
        # Procesar cada registro
        for i, matriz in enumerate(matrices, 1):
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
            
            # Mostrar progreso cada 10 registros
            if i % 10 == 0 or i == matrices.count():
                print(f"Procesados: {i}/{matrices.count()} registros")
        
        # Escribir el archivo JSON
        print(f"Escribiendo archivo: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Obtener información del archivo
        file_size = os.path.getsize(output_file)
        file_size_mb = file_size / (1024 * 1024)
        
        # Generar estadísticas
        stats = generate_statistics(matrices)
        
        print("\n" + "="*50)
        print("✅ EXPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("="*50)
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Registros exportados: {matrices.count()}")
        print(f"💾 Tamaño del archivo: {file_size_mb:.2f} MB")
        print(f"🕒 Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📈 ESTADÍSTICAS:")
        print(f"   • Por Tipología: {stats['por_tipologia']}")
        print(f"   • Activos: {stats['activos']} | Inactivos: {stats['inactivos']}")
        print(f"   • Categorías únicas: {stats['categorias_unicas']}")
        print("="*50)
        
        return {
            'success': True,
            'file': output_file,
            'records': matrices.count(),
            'size_mb': file_size_mb,
            'stats': stats
        }
        
    except Exception as e:
        print(f"❌ Error durante la exportación: {str(e)}")
        return {'success': False, 'error': str(e)}

def generate_statistics(matrices):
    """
    Genera estadísticas de los datos exportados
    
    Args:
        matrices: QuerySet de MatrizCalidad
    
    Returns:
        dict: Estadísticas generadas
    """
    stats = {}
    
    # Estadísticas por tipología
    tipologias = {}
    for tip in matrices.values('tipologia').distinct():
        count = matrices.filter(tipologia=tip['tipologia']).count()
        tipologias[tip['tipologia']] = count
    stats['por_tipologia'] = tipologias
    
    # Estadísticas por estado
    stats['activos'] = matrices.filter(activo=True).count()
    stats['inactivos'] = matrices.filter(activo=False).count()
    
    # Categorías únicas
    stats['categorias_unicas'] = matrices.values('categoria').distinct().count()
    
    return stats

def main():
    """
    Función principal del script
    """
    print("🚀 Script de Exportación de MatrizCalidad")
    print("="*50)
    
    # Permitir especificar nombre de archivo como argumento
    output_file = 'matriz_calidad_export.json'
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    print(f"📄 Archivo de salida: {output_file}")
    
    # Ejecutar exportación
    result = export_matriz_calidad_to_json(output_file)
    
    if result['success']:
        print("\n🎉 Exportación finalizada correctamente")
    else:
        print(f"\n💥 Error en la exportación: {result.get('error', 'Error desconocido')}")
        sys.exit(1)

if __name__ == '__main__':
    main()