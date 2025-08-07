# Generated manually to handle existing data migration and field changes

from django.db import migrations, models


def update_existing_id_preap(apps, schema_editor):
    """Actualiza los ID PreAp existentes para que cumplan con el nuevo formato de 5 dígitos"""
    VentaTarjetaPlata = apps.get_model('tarjeta_plata', 'VentaTarjetaPlata')
    
    # Obtener todas las ventas existentes
    ventas = VentaTarjetaPlata.objects.all()
    
    for i, venta in enumerate(ventas, 1):
        # Generar nuevo ID en formato A0001, A0002, etc.
        letra = chr(ord('A') + (i - 1) // 9999)  # Cambiar letra cada 9999 registros
        numero = ((i - 1) % 9999) + 1
        nuevo_id = f"{letra}{numero:04d}"
        
        # Verificar que el nuevo ID no exista ya
        while VentaTarjetaPlata.objects.filter(id_preap=nuevo_id).exists():
            numero += 1
            if numero > 9999:
                letra = chr(ord(letra) + 1)
                numero = 1
            nuevo_id = f"{letra}{numero:04d}"
        
        # Actualizar el registro
        venta.id_preap = nuevo_id
        venta.save()


def reverse_update_id_preap(apps, schema_editor):
    """Función de reversión - no se puede revertir automáticamente"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tarjeta_plata', '0005_ventatarjetaplata_dn_ventatarjetaplata_entrega_and_more'),
    ]

    operations = [
        # Primero actualizar los datos existentes
        migrations.RunPython(update_existing_id_preap, reverse_update_id_preap),
        # Luego cambiar el campo
        migrations.AlterField(
            model_name='ventatarjetaplata',
            name='id_preap',
            field=models.CharField(blank=True, help_text='ID de preaprobación generado automáticamente por el sistema', max_length=5, unique=True, verbose_name='ID PreAp'),
        ),
    ]