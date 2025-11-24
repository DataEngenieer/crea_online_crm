from django.db import migrations


SQL_CREATE_TABLE = (
    'CREATE TABLE IF NOT EXISTS "calidad_matrizcalidadupgrade" ('
    '"id" bigserial PRIMARY KEY, '
    '"tipologia" varchar(50) NOT NULL, '
    '"categoria" varchar(100) NOT NULL, '
    '"indicador" varchar(255) NOT NULL, '
    '"ponderacion" numeric(5,2) NOT NULL, '
    '"usuario_creacion_id" integer NOT NULL REFERENCES "auth_user" ("id") ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, '
    '"fecha_creacion" timestamp with time zone NOT NULL DEFAULT now(), '
    '"fecha_actualizacion" timestamp with time zone NOT NULL DEFAULT now(), '
    '"activo" boolean NOT NULL DEFAULT TRUE'
    ')'
)


class Migration(migrations.Migration):

    dependencies = [
        ("calidad", "0012_merge_0009_0011"),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE_TABLE),
    ]

