from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Campana
from calidad.models import Auditoria, MatrizCalidad, Speech

class Command(BaseCommand):
    help = 'Configura el módulo de Calidad: crea grupos, permisos y campaña'

    def handle(self, *args, **options):
        # Crear grupo de Calidad
        grupo_calidad, created = Group.objects.get_or_create(name='Calidad')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Calidad" creado exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING('El grupo "Calidad" ya existe')
            )

        # Obtener permisos para los modelos de calidad
        permisos_calidad = []
        
        # Permisos para Auditoria
        content_type_auditoria = ContentType.objects.get_for_model(Auditoria)
        permisos_auditoria = Permission.objects.filter(content_type=content_type_auditoria)
        permisos_calidad.extend(permisos_auditoria)
        
        # Permisos para MatrizCalidad
        content_type_matriz = ContentType.objects.get_for_model(MatrizCalidad)
        permisos_matriz = Permission.objects.filter(content_type=content_type_matriz)
        permisos_calidad.extend(permisos_matriz)
        

        
        # Permisos para Speech
        content_type_speech = ContentType.objects.get_for_model(Speech)
        permisos_speech = Permission.objects.filter(content_type=content_type_speech)
        permisos_calidad.extend(permisos_speech)
        
        # Asignar permisos al grupo
        grupo_calidad.permissions.set(permisos_calidad)
        self.stdout.write(
            self.style.SUCCESS(f'Asignados {len(permisos_calidad)} permisos al grupo Calidad')
        )

        # Crear campaña de Calidad
        campana_calidad, created = Campana.objects.get_or_create(
            codigo='CALIDAD',
            defaults={
                'nombre': 'Calidad',
                'descripcion': 'Módulo de gestión de calidad y auditorías',
                'modulo': 'calidad',
                'activa': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Campaña "Calidad" creada exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING('La campaña "Calidad" ya existe')
            )

        self.stdout.write(
            self.style.SUCCESS('\n=== Configuración del módulo de Calidad completada ===\n')
        )
        
        self.stdout.write('Pasos siguientes:')
        self.stdout.write('1. Asignar usuarios al grupo "Calidad" desde el admin de Django')
        self.stdout.write('2. Asignar usuarios a la campaña "Calidad" desde el admin')
        self.stdout.write('3. Configurar las matrices de calidad desde el módulo')
        self.stdout.write('4. Los usuarios podrán acceder al módulo desde el login')