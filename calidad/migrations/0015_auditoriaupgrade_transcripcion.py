from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calidad', '0014_create_detalleauditoriaupgrade_if_missing'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditoriaupgrade',
            name='transcripcion',
            field=models.TextField(blank=True, null=True),
        ),
    ]

