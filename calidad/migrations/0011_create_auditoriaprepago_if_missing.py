from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("calidad", "0008_alter_matrizcalidadprepago_tipologia_and_more"),
    ]

    operations = [
        # No-op: la tabla AuditoriaPrepago ya se crea en 0007 mediante CreateModel.
        # Esta migración se deja intencionalmente vacía para evitar errores en SQLite.
    ]
