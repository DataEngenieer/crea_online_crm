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
    """
    Crea una comisión automáticamente cuando una venta cambia a estado 'aprobada'.
    """
    # Si la venta ha sido aprobada y no tiene comisión asociada aún
    if instance.estado_revisado == 'aprobada' and not Comision.objects.filter(venta=instance).exists():
        # Calcular monto de comisión fija para este ejemplo
        # El valor real debe basarse en alguna política de la empresa
        monto_comision = 5000  # Valor fijo de ejemplo
        
        # Crear comisión
        Comision.objects.create(
            venta=instance,
            agente=instance.agente,
            valor=monto_comision,  # El campo en el modelo Comision se llama 'valor', no 'monto'
            estado='pendiente',
            fecha_calculo=timezone.now(),
            observaciones=f"Comisión generada automáticamente para la venta #{instance.id}"
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
            if instance.estado_revisado != venta_antigua.estado_revisado:
                # Estos logs pueden ser implementados posteriormente en un sistema de auditoría
                print(f"Venta {instance.id}: Estado cambiado de {venta_antigua.estado_revisado} a {instance.estado_revisado}")
                    
        except VentaPortabilidad.DoesNotExist:
            # Si es nuevo, no hacer nada (el post_save se encargará)
            pass