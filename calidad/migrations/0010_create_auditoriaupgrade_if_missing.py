from django.db import migrations


SQL_CREATE_TABLE = (
    'CREATE TABLE IF NOT EXISTS "calidad_auditoriaupgrade" ('
    '"id" bigserial PRIMARY KEY, '
    '"numero_telefono" varchar(20) NOT NULL, '
    '"fecha_llamada" date NOT NULL, '
    '"observaciones" text NULL, '
    '"tipo_monitoreo" varchar(20) NOT NULL, '
    '"fecha_creacion" timestamp with time zone NOT NULL DEFAULT now(), '
    '"fecha_actualizacion" timestamp with time zone NOT NULL DEFAULT now(), '
    '"puntaje_total" numeric(5,2) NOT NULL DEFAULT 0.0, '
    '"observaciones_tipificacion" text NULL, '
    '"puntaje_ia" varchar(10) NULL, '
    '"resumen_ia" text NULL, '
    '"agente_id" integer NOT NULL REFERENCES "auth_user" ("id") ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED, '
    '"evaluador_id" integer NOT NULL REFERENCES "auth_user" ("id") ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED'
    ')'
)


class Migration(migrations.Migration):

    dependencies = [
        ("calidad", "0008_alter_matrizcalidadprepago_tipologia_and_more"),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE_TABLE),
    ]

