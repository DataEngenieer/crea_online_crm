# Generated by Django 5.2.1 on 2025-07-02 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='aplicativo',
            field=models.CharField(choices=[('CARTERA', 'Cartera'), ('TELEFONICA', 'Telefónica'), ('VICIDIAL', 'Vicidial')], default='CARTERA', help_text='Seleccione el aplicativo relacionado con el ticket', max_length=20, verbose_name='Aplicativo'),
        ),
    ]
