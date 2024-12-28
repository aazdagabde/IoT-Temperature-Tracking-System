from django.apps import AppConfig


class DhtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DHT'




    def ready(self):
        import DHT.signals  # Importer les signaux