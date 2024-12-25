from django.utils import timezone
from .models import Dht11, Incident
from .serializers import DHT11serialize
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import requests

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response


@api_view(["GET", "POST"])
def Dlist(request):
    if request.method == "GET":
        all_data = Dht11.objects.all()
        data_ser = DHT11serialize(all_data, many=True)
        return Response(data_ser.data)

    elif request.method == "POST":
        serial = DHT11serialize(data=request.data)

        if serial.is_valid():
            # On enregistre la nouvelle mesure
            new_dht = serial.save()  # => new_dht est l'objet Dht11 sauvegardé
            current_temp = new_dht.temp

            # Récupérer la mesure précédente pour voir le changement
            previous_dht = Dht11.objects.order_by('-dt').exclude(id=new_dht.id).first()
            if previous_dht:
                previous_temp = previous_dht.temp
            else:
                # Si c'est la première mesure, on peut fixer un "faux" previous_temp = 25
                # afin d'éviter de créer un incident tout de suite
                previous_temp = 25

            # 1) Détection d'un nouveau début d'incident
            if previous_temp <= 25 and current_temp > 25:
                Incident.objects.create(
                    start_dt=new_dht.dt  # Le moment de début
                )

            # 2) Détection de la fin d'un incident
            if previous_temp > 25 and current_temp <= 25:
                # On ferme le dernier incident en cours
                incident_open = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()
                if incident_open:
                    incident_open.end_dt = new_dht.dt
                    incident_open.save()

            # 3) Alertes si current_temp > 25
            if current_temp > 25:
                # Alert Email
                subject = 'Alerte'
                message = 'La température dépasse le seuil de 25°C, veuillez intervenir immédiatement.'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = ['aazdagbousslama@gmail.com']
                send_mail(subject, message, email_from, recipient_list)

                # Alert WhatsApp
                account_sid = 'AC571a2335b3cdd57fba09ce4340f48522'
                auth_token = 'ec4fcca1c74446acdc65f3fe6a7a5682'
                client = Client(account_sid, auth_token)
                message_whatsapp = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body='La température dépasse le seuil de 25°C, veuillez intervenir immédiatement.',
                    to='whatsapp:+212617018560'
                )

                # Alert Telegram
                telegram_token = '7859262503:AAGScp5W3u876LlZk1kcA7_S-dK1bmcuMVw'
                chat_id = '5622689672'
                telegram_message = 'La température dépasse le seuil de 25°C, veuillez intervenir immédiatement.'
                send_telegram_message(telegram_token, chat_id, telegram_message)

            return Response(serial.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)
