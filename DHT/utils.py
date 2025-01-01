
from django.utils import timezone
from datetime import timedelta
from .models import Incident

def filter_incidents_by_param(filter_param):
    """
    Retourne un QuerySet Incident filtré selon filter_param
    qui peut être 'jour', 'semaine', 'mois', 'annee' ou 'all'.
    """
    now = timezone.now()
    if filter_param == 'jour':
        # Dernières 24h
        return Incident.objects.filter(start_dt__gte=now - timedelta(days=1))
    elif filter_param == 'semaine':
        return Incident.objects.filter(start_dt__gte=now - timedelta(weeks=1))
    elif filter_param == 'mois':
        return Incident.objects.filter(start_dt__gte=now - timedelta(days=30))
    elif filter_param == 'annee':
        return Incident.objects.filter(start_dt__gte=now - timedelta(days=365))
    else:
        # 'all' ou paramètre non reconnu
        return Incident.objects.all()
##########################

# DHT/utils.py

from django.utils import timezone
from datetime import timedelta
from .models import Dht11

def filter_data_by_param(filter_param):
    """
    Retourne un QuerySet de Dht11 filtré selon le paramètre choisi:
    - 'jour'    : dernières 24h
    - 'semaine' : derniers 7 jours
    - 'mois'    : derniers 30 jours
    - 'annee'   : derniers 365 jours
    - 'all' ou autre: toutes les mesures
    """
    now = timezone.now()
    qs = Dht11.objects.all().order_by('-dt')

    if filter_param == 'jour':
        return qs.filter(dt__gte=now - timedelta(days=1))
    elif filter_param == 'semaine':
        return qs.filter(dt__gte=now - timedelta(weeks=1))
    elif filter_param == 'mois':
        return qs.filter(dt__gte=now - timedelta(days=30))
    elif filter_param == 'annee':
        return qs.filter(dt__gte=now - timedelta(days=365))
    else:
        # Par défaut : toutes les données
        return qs

##########################