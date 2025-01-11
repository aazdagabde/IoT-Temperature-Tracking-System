# DHT/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Dht11(models.Model):
    temp = models.FloatField(null=True)
    hum = models.FloatField(null=True)
    dt = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"DHT11 mesure ID={self.id} (temp={self.temp}, hum={self.hum})"


class Incident(models.Model):
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    # Supprimé les champs ack et ack_user

    iteration = models.IntegerField(default=0, help_text="Niveau d’escalade de l’incident")

    def __str__(self):
        return f"Incident du {self.start_dt} au {self.end_dt or 'en cours'}"

    @property
    def duration(self):
        if self.end_dt:
            return self.end_dt - self.start_dt
        return None


class Acknowledgment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='acknowledgments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('incident', 'user')

    def __str__(self):
        return f"{self.user.username} a acquitté l'incident {self.incident.id}"



class Profile(models.Model):
    """
    Extension de l’utilisateur pour stocker les identifiants d’alerte
    (Telegram, Twilio, etc.).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.CharField(max_length=255, null=True, blank=True)
    telegram_bot_link = models.CharField(max_length=255, null=True, blank=True, help_text="Lien du bot Telegram")
    twilio_account_sid = models.CharField(max_length=255, null=True, blank=True)
    twilio_auth_token = models.CharField(max_length=255, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

###############""


class GlobalAlertSettings(models.Model):
    telegram_token = models.CharField(max_length=255, null=True, blank=True, help_text="Token du bot Telegram")
    telegram_bot_link = models.CharField(max_length=255, null=True, blank=True, help_text="Lien du bot Telegram")
    smtp_host = models.CharField(max_length=255, null=True, blank=True, help_text="Adresse du serveur SMTP")
    smtp_port = models.IntegerField(null=True, blank=True, help_text="Port SMTP")
    smtp_user = models.CharField(max_length=255, null=True, blank=True, help_text="Utilisateur SMTP")
    smtp_password = models.CharField(max_length=255, null=True, blank=True, help_text="Mot de passe SMTP")
    smtp_use_tls = models.BooleanField(default=True, help_text="Utiliser TLS pour SMTP")
    alert_message = models.TextField(null=True, blank=True, help_text="Message d'alerte par défaut")
    min_temperature = models.FloatField(null=True, blank=True, help_text="Température minimale pour déclencher une alerte")
    max_temperature = models.FloatField(null=True, blank=True, help_text="Température maximale pour déclencher une alerte")
    alerts_enabled = models.BooleanField(default=True, help_text="Activer ou désactiver les alertes")

    def __str__(self):
        return "Paramètres globaux des alertes"

    ####model pour otp##########""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.user.username}"

    def is_valid(self):
        return timezone.now() < self.expires_at