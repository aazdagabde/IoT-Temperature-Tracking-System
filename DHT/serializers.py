from rest_framework import serializers
from .models import Dht11
class DHT11serialize(serializers.ModelSerializer):
 class Meta :
          model = Dht11
          fields ='__all__'


from rest_framework import serializers
from .models import GlobalAlertSettings

class GlobalAlertSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalAlertSettings
        fields = ['telegram_token', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_use_tls']
