# Generated by Django 5.2.1 on 2025-06-25 20:55

import django.db.models.deletion
import tickets.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(help_text='Asunto o título principal del ticket.', max_length=255)),
                ('descripcion', models.TextField(help_text='Descripción detallada del inconveniente o requerimiento.')),
                ('tipo', models.CharField(choices=[('IN', 'Inconveniente'), ('RQ', 'Requerimiento')], default='IN', max_length=2)),
                ('estado', models.CharField(choices=[('AB', 'Abierto'), ('EP', 'En Progreso'), ('PE', 'Pendiente de Tercero'), ('RS', 'Resuelto'), ('CE', 'Cerrado')], default='AB', max_length=2)),
                ('prioridad', models.CharField(choices=[('BA', 'Baja'), ('ME', 'Media'), ('AL', 'Alta'), ('UR', 'Urgente')], default='ME', max_length=2)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('fecha_resolucion', models.DateTimeField(blank=True, help_text='Fecha en que se resolvió el ticket.', null=True)),
                ('fecha_cierre', models.DateTimeField(blank=True, help_text='Fecha en que se cerró el ticket.', null=True)),
                ('asignado_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets_asignados', to=settings.AUTH_USER_MODEL)),
                ('solicitante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets_solicitados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Ticket de Soporte',
                'verbose_name_plural': 'Tickets de Soporte',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='RespuestaTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.TextField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='tickets.ticket')),
            ],
            options={
                'verbose_name': 'Respuesta de Ticket',
                'verbose_name_plural': 'Respuestas de Tickets',
                'ordering': ['fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ArchivoAdjunto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to=tickets.models.ruta_archivo_adjunto)),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                ('respuesta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='adjuntos', to='tickets.respuestaticket')),
                ('ticket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='adjuntos', to='tickets.ticket')),
            ],
            options={
                'verbose_name': 'Archivo Adjunto',
                'verbose_name_plural': 'Archivos Adjuntos',
            },
        ),
    ]
