from django.db import migrations, models
from django.utils.translation import gettext_lazy as _

def combinar_nombres_apellidos(apps, schema_editor):
    # Obtener los modelos
    VentaPortabilidad = apps.get_model('telefonica', 'VentaPortabilidad')
    VentaPrePos = apps.get_model('telefonica', 'VentaPrePos')
    VentaUpgrade = apps.get_model('telefonica', 'VentaUpgrade')
    
    # Actualizar VentaPortabilidad
    for venta in VentaPortabilidad.objects.all():
        venta.nombre_completo = f"{venta.nombres} {venta.apellidos}".strip()
        venta.save(update_fields=['nombre_completo'])
    
    # Actualizar VentaPrePos
    for venta in VentaPrePos.objects.all():
        venta.nombre_completo = f"{venta.nombres} {venta.apellidos}".strip()
        venta.save(update_fields=['nombre_completo'])
    
    # Actualizar VentaUpgrade
    for venta in VentaUpgrade.objects.all():
        venta.nombre_completo = f"{venta.nombres} {venta.apellidos}".strip()
        venta.save(update_fields=['nombre_completo'])


class Migration(migrations.Migration):

    dependencies = [
        ('telefonica', '0005_alter_clientesupgrade_id_base_and_more'),
    ]

    operations = [
        # Primero añadir el campo nombre_completo como nullable
        migrations.AddField(
            model_name='ventaportabilidad',
            name='nombre_completo',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=_('Nombre Completo')),
        ),
        migrations.AddField(
            model_name='ventaprepos',
            name='nombre_completo',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=_('Nombre Completo')),
        ),
        migrations.AddField(
            model_name='ventaupgrade',
            name='nombre_completo',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=_('Nombre Completo')),
        ),
        
        # Luego migrar los datos
        migrations.RunPython(combinar_nombres_apellidos),
        
        # Hacer que el campo nombre_completo sea obligatorio
        migrations.AlterField(
            model_name='ventaportabilidad',
            name='nombre_completo',
            field=models.CharField(max_length=100, verbose_name=_('Nombre Completo')),
        ),
        migrations.AlterField(
            model_name='ventaprepos',
            name='nombre_completo',
            field=models.CharField(max_length=100, verbose_name=_('Nombre Completo')),
        ),
        migrations.AlterField(
            model_name='ventaupgrade',
            name='nombre_completo',
            field=models.CharField(max_length=100, verbose_name=_('Nombre Completo')),
        ),
        
        # Finalmente eliminar los campos antiguos
        migrations.RemoveField(
            model_name='ventaportabilidad',
            name='apellidos',
        ),
        migrations.RemoveField(
            model_name='ventaportabilidad',
            name='nombres',
        ),
        migrations.RemoveField(
            model_name='ventaprepos',
            name='apellidos',
        ),
        migrations.RemoveField(
            model_name='ventaprepos',
            name='nombres',
        ),
        migrations.RemoveField(
            model_name='ventaupgrade',
            name='apellidos',
        ),
        migrations.RemoveField(
            model_name='ventaupgrade',
            name='nombres',
        ),
    ]