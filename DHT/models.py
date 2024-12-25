
# Create your models here.
from django.db import models
class Dht11(models.Model):
  temp = models.FloatField(null=True)
  hum = models.FloatField(null=True)
  dt = models.DateTimeField(auto_now_add=True,null=True)


from django.db import models
from django.contrib.auth.models import User

class Incident(models.Model):
    start_dt = models.DateTimeField()        # Date/heure début
    end_dt = models.DateTimeField(null=True, blank=True)  # Date/heure fin, quand l’incident se termine
    ack = models.BooleanField(default=False) # Acquittement
    remarks = models.TextField(null=True, blank=True)  # Remarque utilisateur

    # Optionnel : enregistrer l’utilisateur qui a acquitté
    ack_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Incident du {self.start_dt} au {self.end_dt or 'en cours'}"

    @property
    def duration(self):
        """
        Calcule la durée (end_dt - start_dt) si end_dt est défini.
        Retourne un objet timedelta ou None.
        """
        if self.end_dt:
            return self.end_dt - self.start_dt
        return None
