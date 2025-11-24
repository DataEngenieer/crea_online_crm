from django.db import migrations


SQL_CREATE_TABLE = (
    'CREATE TABLE IF NOT EXISTS "calidad_detalleauditoriaupgrade" ('
    '"id" bigserial PRIMARY KEY, '
    '"auditoria_id" integer NOT NULL REFERENCES "calidad_auditoriaupgrade" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED, '
    '"indicador_id" integer NOT NULL REFERENCES "calidad_matrizcalidadupgrade" ("id") ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, '
    '"cumple" boolean NOT NULL DEFAULT FALSE, '
    '"observaciones" text NULL, '
    '"fecha_creacion" timestamp with time zone NOT NULL DEFAULT now(), '
    '"fecha_actualizacion" timestamp with time zone NOT NULL DEFAULT now(), '
    'UNIQUE ("auditoria_id", "indicador_id")'
    ')'
)


class Migration(migrations.Migration):

    dependencies = [
        ("calidad", "0013_create_matrizcalidadupgrade_if_missing"),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE_TABLE),
    ]

