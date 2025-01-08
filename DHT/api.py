from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Dht11, Incident, Profile, Acknowledgment
from .alerts import send_telegram_alert, send_whatsapp_alert, send_email_alert


@api_view(['GET','POST'])
def Dlist(request):
    """
    - GET : Renvoie la liste des mesures DHT11 en JSON.
    - POST : Reçoit une nouvelle mesure (temp, hum) depuis l’ESP8266,
             puis gère l’ouverture/fermeture d’incident + escalade.
    """
    if request.method == 'GET':
        queryset = Dht11.objects.all().order_by('-dt')
        data = [
            {
                'id': d.id,
                'temp': d.temp,
                'hum': d.hum,
                'dt': d.dt
            }
            for d in queryset
        ]
        return Response(data)

    elif request.method == 'POST':
        # Supposons que l’ESP8266 envoie un JSON {"temp": 30, "hum": 60}
        temp = request.data.get('temp')
        hum = request.data.get('hum')

        # 1. Enregistrer la nouvelle mesure
        if temp is not None and hum is not None:
            Dht11.objects.create(temp=temp, hum=hum)

            # 2. Vérifier la température et gérer l’incident
            check_temperature_and_manage_incident(float(temp))
            return Response({"status": "OK", "message": "Mesure enregistrée."})
        else:
            return Response({"status": "ERROR", "message": "Paramètres 'temp' ou 'hum' manquants."}, status=400)

    return Response({"status": "ERROR", "message": "Méthode non prise en charge."}, status=405)


def check_temperature_and_manage_incident(current_temp):
    """
    - current_temp : float, la température reçue
    - Gère la création/fermeture d’incident + escalade en fonction
      de la température et de l’état actuel (incident ouvert ou non).
    """
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()

    # Seuil de 25°C pour fermer l'incident (ou ne rien faire si aucun incident ouvert)
    if current_temp <= 25:
        if open_incident:
            open_incident.end_dt = timezone.now()
            open_incident.save()
            print("[INFO] Incident fermé (température redevenue normale).")
        else:
            print("[INFO] Aucun incident en cours, température normale.")
    else:
        # Température élevée
        if not open_incident:
            # 1. Créer un nouvel incident avec iteration=1
            new_incident = Incident.objects.create(
                start_dt=timezone.now(),
                iteration=1
            )
            print(f"[INFO] Nouvel incident créé (ID={new_incident.id}). Itération=1")

            # Alerter le(s) user(s) concernés à l’itération 1 -> user1
            users_to_alert = get_users_to_alert(new_incident)
            send_custom_alerts(new_incident, users_to_alert)
        else:
            # Incident déjà en cours
            # Vérifier s'il reste des utilisateurs non acquittés
            users_to_alert = get_users_to_alert(open_incident)
            if users_to_alert:
                # Incrémenter l'itération si l'on doit relancer
                open_incident.iteration += 1
                open_incident.save()
                print(f"[INFO] Incident en cours (ID={open_incident.id}) -> Itération={open_incident.iteration}")

                # Rappeler user1 s'il n'a pas acquitté, ajouter user2, etc.
                users_to_alert = get_users_to_alert(open_incident)
                send_custom_alerts(open_incident, users_to_alert)
            else:
                print("[INFO] Tous les utilisateurs ont acquitté l'incident. Pas d'escalade.")
                # Optionnel : on peut fermer l’incident s'il est jugé inutile de poursuivre
                # open_incident.end_dt = timezone.now()
                # open_incident.save()


def get_users_to_alert(incident):
    """
    Retourne la liste des utilisateurs à alerter en fonction de l'itération.
    - iteration=1 -> on alerte l'index 0 (user1) s'il n'a pas acquitté
    - iteration=2 -> on alerte l'index 0 (user1) s'il n'a pas acquitté + index 1 (user2) s'il n'a pas acquitté
    - iteration=3 -> user1, user2, user3 (s'ils n'ont pas acquitté), etc.
    """
    iteration = incident.iteration
    escalation_order = ['user1', 'user2', 'user3', 'admin']  # Ordre d'escalade
    users_to_alert = []

    # On boucle de 0 à iteration-1
    for i in range(iteration):
        if i < len(escalation_order):
            username = escalation_order[i]
            user = get_user_by_username(username)
            if user:
                # Vérifier s'il a déjà acquitté (Acknowledgment)
                already_ack = Acknowledgment.objects.filter(incident=incident, user=user).exists()
                if not already_ack:
                    users_to_alert.append(user)

    return users_to_alert


def send_custom_alerts(incident, users):
    """
    Envoie des alertes personnalisées aux utilisateurs spécifiés.
    """
    for user in users:
        message = (
            f"Alerte: température élevée, veuillez intervenir immédiatement pour vérifier "
            f"et corriger cette situation (Incident #{incident.id}, itération {incident.iteration}, "
            f"utilisateur : {user.username})."
        )
        notify_user(user, message)


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

    # Telegram
    telegram_bot_token = "7852205995:AAHeF8A_WPbY4rfSYmfgZc3OSc_OSTbOues"
    if profile.telegram_id:
        send_telegram_alert(telegram_bot_token, profile.telegram_id, message)

    # WhatsApp
    """
    if (
        profile.twilio_account_sid and
        profile.twilio_auth_token and
        profile.whatsapp_number
    ):
        send_whatsapp_alert(
            account_sid=profile.twilio_account_sid,
            auth_token=profile.twilio_auth_token,
            from_whatsapp='whatsapp:+14155238886',  # Numéro WhatsApp Sandbox Twilio, par ex.
            to_whatsapp=f'whatsapp:{profile.whatsapp_number}',
            message=message
        )
    """

    # E-mail
    if user.email:
        send_email_alert(
            subject="Alerte Température Élevée",
            body=message,
            recipients=[user.email]
        )


def get_user_by_username(username):
    """
    Récupère un User Django par son username, ou None s'il n'existe pas.
    """
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None
