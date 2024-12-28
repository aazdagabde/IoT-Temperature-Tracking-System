

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User
from .serializers import DHT11serialize

from .models import Dht11, Incident
from .alerts import (
    send_telegram_alert,
    send_whatsapp_alert,
    send_email_alert
)

@api_view(['GET','POST'])
def Dlist(request):
    """
    - GET : Renvoie la liste des mesures DHT11 en JSON.
    - POST : Reçoit une nouvelle mesure (temp, hum) depuis l’ESP8266.
             Puis gère l’ouverture/fermeture d’incident + escalade.
    """
    if request.method == 'GET':
        all_data = Dht11.objects.all()
        data_ser = DHT11serialize(all_data, many=True)
        return Response(data_ser.data)

    elif request.method == 'POST':
        # Supposons que l’ESP8266 envoie un JSON {"temp": 30, "hum": 60}
        temp = request.data.get('temp')
        hum = request.data.get('hum')

        # 1. Enregistrer la nouvelle mesure
        if temp is not None and hum is not None:
            new_dht = Dht11.objects.create(temp=temp, hum=hum)
            # 2. Vérifier la température et gérer l’incident
            check_temperature_and_manage_incident(float(temp))
            return Response({"status": "OK", "message": "Mesure enregistrée."})
        else:
            return Response({"status": "ERROR", "message": "Paramètres temp ou hum manquants."}, status=400)

    return Response({"status": "ERROR", "message": "Méthode non prise en charge."}, status=405)


def check_temperature_and_manage_incident(current_temp):
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()

    if current_temp <= 25:
        if open_incident:
            open_incident.end_dt = timezone.now()
            open_incident.save()
            logger.info(f"Incident {open_incident.id} fermé (température redevenue normale).")
    else:
        if not open_incident:
            try:
                new_incident = Incident.objects.create(
                    start_dt=timezone.now(),
                    iteration=1
                )
                logger.info(f"Nouvel incident créé (ID={new_incident.id}). Itération=1")
                send_iteration_alerts(new_incident)
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'incident: {e}")
        else:
            try:
                # Toujours escalader, même si ack=True
                open_incident.iteration += 1
                open_incident.ack = False  # Réinitialiser ack pour permettre l'escalade
                open_incident.save()
                logger.info(f"Incident en cours (ID={open_incident.id}) -> Itération={open_incident.iteration}")
                send_iteration_alerts(open_incident)
            except Exception as e:
                logger.error(f"Erreur lors de l'escalade de l'incident {open_incident.id}: {e}")



def send_iteration_alerts(incident: Incident):
    """
    Envoie des alertes selon incident.iteration.
    - user1 : itération 1
    - user2 : itération 2
    - user3 : itération 3
    - admin : itération 4
    etc.
    Hardcodé pour l'exemple, adaptez à vos besoins ou via Profile.
    """
    iteration = incident.iteration
    message = f"Alerte: température élevée (Incident #{incident.id}, itération {iteration})."

    user1 = get_user_by_username("user1")
    user2 = get_user_by_username("user2")
    user3 = get_user_by_username("user3")
    admin = get_user_by_username("admin")

    if iteration == 1:
        # Alerte à user1
        notify_user(user1, message)
    elif iteration == 2:
        # user1 (si pas acquitté) et user2
        if not incident.ack:
            notify_user(user1, message)
        notify_user(user2, message)
    elif iteration == 3:
        # user1 & user2 (si pas acquitté), user3
        if not incident.ack:
            notify_user(user1, message)
            notify_user(user2, message)
        notify_user(user3, message)
    elif iteration == 4:
        # user1, user2, user3 (si pas acquitté), admin
        if not incident.ack:
            notify_user(user1, message)
            notify_user(user2, message)
            notify_user(user3, message)
        notify_user(admin, message)
    else:
        # itération > 4 => à vous de voir la logique
        pass


def notify_user(user, message: str):
    """
    Envoie l'alerte (Telegram, WhatsApp, e-mail) si l'utilisateur a un Profile
    configuré (telegram_id, twilio, etc.).
    """
    if not user:
        return
    profile = getattr(user, 'profile', None)
    if not profile:
        print(f"[WARN] L'utilisateur {user.username} n'a pas de profil configuré.")
        return

    # Ex. Telegram
    telegram_bot_token = "7859262503:AAGScp5W3u876LlZk1kcA7_S-dK1bmcuMVw"  # ou en variable d’env.
    if profile.telegram_id:
        send_telegram_alert(telegram_bot_token, profile.telegram_id, message)

    # Ex. WhatsApp
    """
    if profile.twilio_account_sid and profile.twilio_auth_token and profile.whatsapp_number:
        send_whatsapp_alert(
            account_sid=profile.twilio_account_sid,
            auth_token=profile.twilio_auth_token,
            from_whatsapp='whatsapp:+14155238886',
            to_whatsapp=f'whatsapp:{profile.whatsapp_number}',
            message=message
        )
    """

    # Ex. E-mail
    if user.email:
        send_email_alert(
            subject="Alerte Température Élevée",
            body=message,
            recipients=[user.email]
        )


def get_user_by_username(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None
