# Generated by Django 5.2.1 on 2025-06-11 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_gestion_observaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='acuerdopago',
            name='referencia_producto',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Referencia de Producto'),
        ),
    ]
