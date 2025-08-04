from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Campana
from tarjeta_plata.models import ClienteTarjetaPlata, VentaTarjetaPlata, GestionBackofficeTarjetaPlata, AuditoriaBackofficeTarjetaPlata


class Command(BaseCommand):
    help = 'Configura el módulo Tarjeta Plata con datos iniciales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Crear grupos de usuarios para Tarjeta Plata',
        )
        parser.add_argument(
            '--create-campaign',
            action='store_true',
            help='Crear campaña inicial para Tarjeta Plata',
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Crear datos de prueba',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuración del módulo Tarjeta Plata...')
        )

        if options['create_groups']:
            self.create_groups()

        if options['create_campaign']:
            self.create_campaign()

        if options['create_test_data']:
            self.create_test_data()

        self.stdout.write(
            self.style.SUCCESS('Configuración del módulo Tarjeta Plata completada.')
        )

    def create_groups(self):
        """Crear grupos de usuarios para el módulo Tarjeta Plata"""
        self.stdout.write('Creando grupos de usuarios...')

        # Obtener content types para los modelos de tarjeta_plata
        cliente_ct = ContentType.objects.get_for_model(ClienteTarjetaPlata)
        venta_ct = ContentType.objects.get_for_model(VentaTarjetaPlata)
        gestion_ct = ContentType.objects.get_for_model(GestionBackofficeTarjetaPlata)
        auditoria_ct = ContentType.objects.get_for_model(AuditoriaBackofficeTarjetaPlata)

        # Grupo: Asesores Tarjeta Plata
        asesor_group, created = Group.objects.get_or_create(
            name='Asesores Tarjeta Plata'
        )
        if created:
            self.stdout.write(f'  ✓ Grupo creado: {asesor_group.name}')
        else:
            self.stdout.write(f'  - Grupo ya existe: {asesor_group.name}')

        # Permisos para asesores
        asesor_permissions = [
            # Clientes
            Permission.objects.get(content_type=cliente_ct, codename='view_clientetarjetaplata'),
            Permission.objects.get(content_type=cliente_ct, codename='add_clientetarjetaplata'),
            Permission.objects.get(content_type=cliente_ct, codename='change_clientetarjetaplata'),
            # Ventas
            Permission.objects.get(content_type=venta_ct, codename='view_ventatarjetaplata'),
            Permission.objects.get(content_type=venta_ct, codename='add_ventatarjetaplata'),
            Permission.objects.get(content_type=venta_ct, codename='change_ventatarjetaplata'),
        ]
        asesor_group.permissions.set(asesor_permissions)

        # Grupo: Backoffice Tarjeta Plata
        backoffice_group, created = Group.objects.get_or_create(
            name='Backoffice Tarjeta Plata'
        )
        if created:
            self.stdout.write(f'  ✓ Grupo creado: {backoffice_group.name}')
        else:
            self.stdout.write(f'  - Grupo ya existe: {backoffice_group.name}')

        # Permisos para backoffice (todos los permisos)
        backoffice_permissions = [
            # Clientes
            Permission.objects.get(content_type=cliente_ct, codename='view_clientetarjetaplata'),
            Permission.objects.get(content_type=cliente_ct, codename='add_clientetarjetaplata'),
            Permission.objects.get(content_type=cliente_ct, codename='change_clientetarjetaplata'),
            Permission.objects.get(content_type=cliente_ct, codename='delete_clientetarjetaplata'),
            # Ventas
            Permission.objects.get(content_type=venta_ct, codename='view_ventatarjetaplata'),
            Permission.objects.get(content_type=venta_ct, codename='add_ventatarjetaplata'),
            Permission.objects.get(content_type=venta_ct, codename='change_ventatarjetaplata'),
            Permission.objects.get(content_type=venta_ct, codename='delete_ventatarjetaplata'),
            # Gestión
            Permission.objects.get(content_type=gestion_ct, codename='view_gestionbackofficetarjetaplata'),
            Permission.objects.get(content_type=gestion_ct, codename='add_gestionbackofficetarjetaplata'),
            Permission.objects.get(content_type=gestion_ct, codename='change_gestionbackofficetarjetaplata'),
            Permission.objects.get(content_type=gestion_ct, codename='delete_gestionbackofficetarjetaplata'),
            # Auditoría
            Permission.objects.get(content_type=auditoria_ct, codename='view_auditoriabackofficetarjetaplata'),
            Permission.objects.get(content_type=auditoria_ct, codename='add_auditoriabackofficetarjetaplata'),
            Permission.objects.get(content_type=auditoria_ct, codename='change_auditoriabackofficetarjetaplata'),
            Permission.objects.get(content_type=auditoria_ct, codename='delete_auditoriabackofficetarjetaplata'),
        ]
        backoffice_group.permissions.set(backoffice_permissions)

        # Grupo: Supervisores Tarjeta Plata
        supervisor_group, created = Group.objects.get_or_create(
            name='Supervisores Tarjeta Plata'
        )
        if created:
            self.stdout.write(f'  ✓ Grupo creado: {supervisor_group.name}')
        else:
            self.stdout.write(f'  - Grupo ya existe: {supervisor_group.name}')

        # Supervisores tienen todos los permisos
        supervisor_group.permissions.set(backoffice_permissions)

        self.stdout.write(self.style.SUCCESS('Grupos de usuarios creados exitosamente.'))

    def create_campaign(self):
        """Crear campaña inicial para Tarjeta Plata"""
        self.stdout.write('Creando campaña inicial...')

        campana, created = Campana.objects.get_or_create(
            codigo='TARJETA_PLATA_MX',
            defaults={
                'nombre': 'Tarjeta Plata México',
                'descripcion': 'Campaña para venta de tarjetas de crédito Plata en México',
                'modulo': 'tarjeta_plata',
                'activa': True,
            }
        )

        if created:
            self.stdout.write(f'  ✓ Campaña creada: {campana.nombre}')
        else:
            self.stdout.write(f'  - Campaña ya existe: {campana.nombre}')

        self.stdout.write(self.style.SUCCESS('Campaña creada exitosamente.'))

    def create_test_data(self):
        """Crear datos de prueba para el módulo"""
        self.stdout.write('Creando datos de prueba...')

        # Crear clientes de prueba
        clientes_data = [
            {
                'telefono': '5551234567',
                'nombre_completo': 'Juan Pérez García',
                'rfc': 'PEGJ850101ABC',
                'email': 'juan.perez@email.com',
                'factibilidad': 'factible',
                'tipo': 'prospecto',
                'genero': 'M',
            },
            {
                'telefono': '5559876543',
                'nombre_completo': 'María González López',
                'rfc': 'GOLM900215DEF',
                'email': 'maria.gonzalez@email.com',
                'factibilidad': 'factible',
                'tipo': 'cliente',
                'genero': 'F',
            },
            {
                'telefono': '5555555555',
                'nombre_completo': 'Carlos Rodríguez Martínez',
                'rfc': 'ROMC750320GHI',
                'email': 'carlos.rodriguez@email.com',
                'factibilidad': 'pendiente',
                'tipo': 'lead',
                'genero': 'M',
            },
        ]

        for cliente_data in clientes_data:
            cliente, created = ClienteTarjetaPlata.objects.get_or_create(
                telefono=cliente_data['telefono'],
                defaults=cliente_data
            )
            if created:
                self.stdout.write(f'  ✓ Cliente creado: {cliente.nombre_completo}')
            else:
                self.stdout.write(f'  - Cliente ya existe: {cliente.nombre_completo}')

        # Crear usuario de prueba si no existe
        try:
            user_admin = User.objects.get(username='admin')
        except User.DoesNotExist:
            user_admin = User.objects.create_user(
                username='admin',
                email='admin@tarjetaplata.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write('  ✓ Usuario admin creado')

        # Crear ventas de prueba
        ventas_data = [
            {
                'id_preap': 'PREAP001234567',
                'item': 'CLI001',
                'nombre': 'María González López',
                'ine': 'GOLM850315MDFNNN01',
                'rfc': 'GOLM850315ABC',
                'telefono': '5551111111',
                'correo': 'maria.gonzalez@email.com',
                'direccion': 'Av. Insurgentes 123, Col. Roma Norte',
                'codigo_postal': '06700',
                'estado_venta': 'nueva',
                'agente': user_admin,
            },
            {
                'id_preap': 'PREAP001234568',
                'item': 'CLI002',
                'nombre': 'Roberto Silva Torres',
                'ine': 'SITR900215HDFNNN02',
                'rfc': 'SITR900215DEF',
                'telefono': '5552222222',
                'correo': 'roberto.silva@email.com',
                'direccion': 'Calle Madero 456, Col. Centro',
                'codigo_postal': '06000',
                'estado_venta': 'aceptada',
                'agente': user_admin,
            },
        ]

        for venta_data in ventas_data:
            # Verificar si ya existe una venta con el mismo teléfono
            if not VentaTarjetaPlata.objects.filter(telefono=venta_data['telefono']).exists():
                venta = VentaTarjetaPlata.objects.create(**venta_data)
                self.stdout.write(f'  ✓ Venta creada: {venta.nombre} - {venta.id_preap}')
            else:
                self.stdout.write(f'  - Venta ya existe para teléfono: {venta_data["telefono"]}')

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados exitosamente.'))

    def create_permissions(self):
        """Crear permisos personalizados si es necesario"""
        # Los permisos básicos se crean automáticamente con las migraciones
        # Aquí se pueden agregar permisos personalizados si es necesario
        pass