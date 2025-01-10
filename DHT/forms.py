# DHT/forms.py

from django import forms
from .models import GlobalAlertSettings

class GlobalAlertSettingsForm(forms.ModelForm):
    class Meta:
        model = GlobalAlertSettings
        fields = '__all__'