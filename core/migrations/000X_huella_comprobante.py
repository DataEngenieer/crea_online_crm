from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HuellaComprobante',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('accion', models.CharField(max_length=20, choices=[('descarga', 'Descarga'), ('envio', 'Envío')])),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('correo_destino', models.EmailField(blank=True, null=True)),
                ('comprobante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Comprobante')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True, blank=True)),
            ],
        ),
    ]
