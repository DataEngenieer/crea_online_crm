from django.apps import AppConfig


class TelefonicaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telefonica'
    verbose_name = 'Telefónica Portal'
    
    def ready(self):
        import telefonica.signals  # Importa las señales al iniciar la aplicación