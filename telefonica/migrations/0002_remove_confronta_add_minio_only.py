# Generated migration for MinIO-only storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telefonica', '0001_initial'),
    ]

    operations = [
        # Agregar nuevos campos de MinIO
        migrations.AddField(
            model_name='ventaportabilidad',
            name='confronta_nombre_original',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre Original del Archivo'),
        ),
        migrations.AddField(
            model_name='ventaportabilidad',
            name='confronta_tipo_archivo',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Tipo de Archivo'),
        ),
        # Eliminar el campo FileField local
        migrations.RemoveField(
            model_name='ventaportabilidad',
            name='confronta',
        ),
    ]