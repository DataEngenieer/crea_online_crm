from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import VentaPortabilidad, VentaPrePos, VentaUpgrade, Comision
from django.utils import timezone

"""
Archivo de señales para la aplicación Telefónica.
Maneja eventos automáticos cuando se crean o modifican registros.
"""

@receiver(post_save, sender=VentaPortabilidad)
def crear_comision_venta(sender, instance, created, **kwargs):
    """Crear comisión automáticamente cuando una venta es aprobada"""
    if instance.estado_venta == 'aprobada':
        # Verificar si ya existe una comisión para esta venta
        if not Comision.objects.filter(venta=instance).exists():
            Comision.objects.create(
                agente=instance.agente,
                venta=instance,
                monto=5000,  # Valor fijo por ahora
                estado='pendiente'
            )

@receiver(pre_save, sender=VentaPortabilidad)
def actualizar_fechas_estados(sender, instance, **kwargs):
    """
    Actualiza fechas automáticamente según los cambios de estado.
    """
    # Si es un objeto existente
    if instance.id:
        try:
            # Obtener versión anterior de la venta
            venta_antigua = VentaPortabilidad.objects.get(id=instance.id)
            
            # Si cambió el estado revisado, actualizar la fecha de actualización
            # El modelo Venta tiene auto_now=True en fecha_actualizacion, por lo que se actualiza automáticamente
            # Solo agregamos logs para depuración
            if instance.estado_venta != venta_antigua.estado_venta:
                # Estos logs pueden ser implementados posteriormente en un sistema de auditoría
                print(f"Venta {instance.id}: Estado cambiado de {venta_antigua.estado_venta} a {instance.estado_venta}")
                    
        except VentaPortabilidad.DoesNotExist:
            # Si es nuevo, no hacer nada (el post_save se encargará)
            pass