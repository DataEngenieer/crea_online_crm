# core/management/commands/manage_ips.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.models import IPPermitida, RegistroAccesoIP
import requests
import json


class Command(BaseCommand):
    help = 'Gestiona las IPs permitidas en el sistema'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Acciones disponibles')
        
        # Subcomando para listar IPs
        list_parser = subparsers.add_parser('list', help='Lista todas las IPs permitidas')
        list_parser.add_argument(
            '--active-only',
            action='store_true',
            help='Mostrar solo IPs activas'
        )
        
        # Subcomando para agregar IP
        add_parser = subparsers.add_parser('add', help='Agrega una nueva IP permitida')
        add_parser.add_argument('ip', help='Dirección IP a agregar')
        add_parser.add_argument('description', help='Descripción de la IP')
        add_parser.add_argument(
            '--user',
            help='Username del usuario que crea la IP (opcional)'
        )
        
        # Subcomando para eliminar IP
        remove_parser = subparsers.add_parser('remove', help='Elimina una IP permitida')
        remove_parser.add_argument('ip', help='Dirección IP a eliminar')
        
        # Subcomando para activar/desactivar IP
        toggle_parser = subparsers.add_parser('toggle', help='Activa o desactiva una IP')
        toggle_parser.add_argument('ip', help='Dirección IP a activar/desactivar')
        
        # Subcomando para consultar información de IP
        info_parser = subparsers.add_parser('info', help='Consulta información de una IP')
        info_parser.add_argument('ip', help='Dirección IP a consultar')
        
        # Subcomando para ver estadísticas
        stats_parser = subparsers.add_parser('stats', help='Muestra estadísticas de acceso')
        stats_parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días para las estadísticas (default: 7)'
        )
        
        # Subcomando para limpiar registros antiguos
        cleanup_parser = subparsers.add_parser('cleanup', help='Limpia registros antiguos')
        cleanup_parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Eliminar registros más antiguos que X días (default: 90)'
        )
        cleanup_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar la eliminación sin preguntar'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_ips(options['active_only'])
        elif action == 'add':
            self.add_ip(options['ip'], options['description'], options.get('user'))
        elif action == 'remove':
            self.remove_ip(options['ip'])
        elif action == 'toggle':
            self.toggle_ip(options['ip'])
        elif action == 'info':
            self.get_ip_info(options['ip'])
        elif action == 'stats':
            self.show_stats(options['days'])
        elif action == 'cleanup':
            self.cleanup_records(options['days'], options['confirm'])
        else:
            self.print_help('manage.py', 'manage_ips')

    def list_ips(self, active_only=False):
        """Lista todas las IPs permitidas."""
        ips = IPPermitida.objects.all()
        if active_only:
            ips = ips.filter(activa=True)
        
        if not ips.exists():
            self.stdout.write(
                self.style.WARNING('No hay IPs permitidas registradas.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'\nIPs Permitidas ({ips.count()} total):')
        )
        self.stdout.write('-' * 80)
        
        for ip in ips:
            status = self.style.SUCCESS('ACTIVA') if ip.activa else self.style.ERROR('INACTIVA')
            ultimo_acceso = ip.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if ip.ultimo_acceso else 'Nunca'
            
            self.stdout.write(
                f'IP: {ip.ip_address:15} | Estado: {status} | '
                f'Descripción: {ip.descripcion[:30]:30} | '
                f'Último acceso: {ultimo_acceso}'
            )

    def add_ip(self, ip_address, description, username=None):
        """Agrega una nueva IP permitida."""
        # Verificar si la IP ya existe
        if IPPermitida.objects.filter(ip_address=ip_address).exists():
            raise CommandError(f'La IP {ip_address} ya está registrada.')
        
        # Obtener usuario si se especifica
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'Usuario "{username}" no encontrado.')
        
        # Crear la IP permitida
        ip_permitida = IPPermitida.objects.create(
            ip_address=ip_address,
            descripcion=description,
            usuario_creacion=user
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'IP {ip_address} agregada exitosamente.\n'
                f'Descripción: {description}\n'
                f'Creada por: {user.username if user else "Sistema"}'
            )
        )

    def remove_ip(self, ip_address):
        """Elimina una IP permitida."""
        try:
            ip_permitida = IPPermitida.objects.get(ip_address=ip_address)
            ip_permitida.delete()
            self.stdout.write(
                self.style.SUCCESS(f'IP {ip_address} eliminada exitosamente.')
            )
        except IPPermitida.DoesNotExist:
            raise CommandError(f'IP {ip_address} no encontrada.')

    def toggle_ip(self, ip_address):
        """Activa o desactiva una IP."""
        try:
            ip_permitida = IPPermitida.objects.get(ip_address=ip_address)
            ip_permitida.activa = not ip_permitida.activa
            ip_permitida.save()
            
            estado = 'activada' if ip_permitida.activa else 'desactivada'
            self.stdout.write(
                self.style.SUCCESS(f'IP {ip_address} {estado} exitosamente.')
            )
        except IPPermitida.DoesNotExist:
            raise CommandError(f'IP {ip_address} no encontrada.')

    def get_ip_info(self, ip_address):
        """Consulta información de una IP usando la API."""
        self.stdout.write(f'Consultando información de {ip_address}...')
        
        try:
            response = requests.get(f'https://api.ipquery.io/{ip_address}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                self.stdout.write(self.style.SUCCESS('\nInformación de la IP:'))
                self.stdout.write('-' * 50)
                
                # Información básica
                self.stdout.write(f'IP: {data.get("ip", "N/A")}')
                
                # Ubicación
                location = data.get('location', {})
                if location:
                    self.stdout.write(f'País: {location.get("country", "N/A")}')
                    self.stdout.write(f'Ciudad: {location.get("city", "N/A")}')
                    self.stdout.write(f'Región: {location.get("state", "N/A")}')
                    self.stdout.write(f'Zona horaria: {location.get("timezone", "N/A")}')
                
                # ISP
                isp_info = data.get('isp', {})
                if isp_info:
                    self.stdout.write(f'ISP: {isp_info.get("isp", "N/A")}')
                    self.stdout.write(f'Organización: {isp_info.get("org", "N/A")}')
                    self.stdout.write(f'ASN: {isp_info.get("asn", "N/A")}')
                
                # Análisis de riesgo
                risk = data.get('risk', {})
                if risk:
                    self.stdout.write('\nAnálisis de Riesgo:')
                    self.stdout.write(f'VPN: {"Sí" if risk.get("is_vpn") else "No"}')
                    self.stdout.write(f'Proxy: {"Sí" if risk.get("is_proxy") else "No"}')
                    self.stdout.write(f'Tor: {"Sí" if risk.get("is_tor") else "No"}')
                    self.stdout.write(f'Datacenter: {"Sí" if risk.get("is_datacenter") else "No"}')
                    self.stdout.write(f'Puntuación de riesgo: {risk.get("risk_score", 0)}%')
                
            else:
                raise CommandError(f'Error al consultar la API: {response.status_code}')
                
        except requests.RequestException as e:
            raise CommandError(f'Error de conexión: {str(e)}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Error al procesar la respuesta: {str(e)}')

    def show_stats(self, days):
        """Muestra estadísticas de acceso."""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=days)
        
        # Estadísticas generales
        total_registros = RegistroAccesoIP.objects.filter(fecha_acceso__gte=fecha_limite).count()
        logins_exitosos = RegistroAccesoIP.objects.filter(
            fecha_acceso__gte=fecha_limite,
            tipo_acceso='login_exitoso'
        ).count()
        logins_fallidos = RegistroAccesoIP.objects.filter(
            fecha_acceso__gte=fecha_limite,
            tipo_acceso='login_fallido'
        ).count()
        ips_bloqueadas = RegistroAccesoIP.objects.filter(
            fecha_acceso__gte=fecha_limite,
            tipo_acceso='ip_bloqueada'
        ).count()
        
        self.stdout.write(
            self.style.SUCCESS(f'\nEstadísticas de los últimos {days} días:')
        )
        self.stdout.write('-' * 50)
        self.stdout.write(f'Total de registros: {total_registros}')
        self.stdout.write(f'Logins exitosos: {logins_exitosos}')
        self.stdout.write(f'Logins fallidos: {logins_fallidos}')
        self.stdout.write(f'IPs bloqueadas: {ips_bloqueadas}')
        
        # Top IPs
        from django.db.models import Count
        top_ips = RegistroAccesoIP.objects.filter(
            fecha_acceso__gte=fecha_limite
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        if top_ips:
            self.stdout.write('\nTop 10 IPs más activas:')
            for i, ip_data in enumerate(top_ips, 1):
                self.stdout.write(f'{i:2}. {ip_data["ip_address"]:15} - {ip_data["count"]} accesos')

    def cleanup_records(self, days, confirm):
        """Limpia registros antiguos."""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=days)
        registros_antiguos = RegistroAccesoIP.objects.filter(fecha_acceso__lt=fecha_limite)
        count = registros_antiguos.count()
        
        if count == 0:
            self.stdout.write(
                self.style.WARNING(f'No hay registros más antiguos que {days} días.')
            )
            return
        
        if not confirm:
            respuesta = input(
                f'¿Está seguro de eliminar {count} registros más antiguos que {days} días? (s/N): '
            )
            if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write('Operación cancelada.')
                return
        
        registros_antiguos.delete()
        self.stdout.write(
            self.style.SUCCESS(f'{count} registros eliminados exitosamente.')
        )