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
    twilio_account_sid = models.CharField(max_length=255, null=True, blank=True)
    twilio_auth_token = models.CharField(max_length=255, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=50, null=True, blank=True)

    # Ajoutez d’autres champs si besoin

    def __str__(self):
        return f"Profil de {self.user.username}"
