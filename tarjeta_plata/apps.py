from django.apps import AppConfig


class TarjetaPlataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tarjeta_plata'
    verbose_name = 'Tarjeta Plata - Crédito México'
    
    def ready(self):
        # Importar señales si las necesitamos en el futuro
        pass
