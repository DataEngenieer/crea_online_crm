from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("calidad", "0013_create_matrizcalidadupgrade_if_missing"),
    ]

    operations = [
        # No-op: la tabla DetalleAuditoriaUpgrade se crea en 0007 con CreateModel.
    ]
