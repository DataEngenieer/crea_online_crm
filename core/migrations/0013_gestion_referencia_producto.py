# Generated by Django 5.2.1 on 2025-06-13 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_acuerdopago_referencia_producto'),
    ]

    operations = [
        migrations.AddField(
            model_name='gestion',
            name='referencia_producto',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Referencia de Producto'),
        ),
    ]
