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
    - POST : Reçoit une nouvelle mesure (temp, hum) depuis l’ESP8266.
             Puis gère l’ouverture/fermeture d’incident + escalade.
    """
    if request.method == 'GET':
        queryset = Dht11.objects.all().order_by('-dt')
        data = [
            {
                'id': d.id,
                'temp': d.temp,
                'hum': d.hum,
                'dt': d.dt
            } for d in queryset
        ]
        return Response(data)

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
    """
    - current_temp : float, la température reçue
    - Gère la création/fermeture d’incident + escalade en fonction
      de la température et de l’état actuel (incident ouvert ou non).
    """
    open_incident = Incident.objects.filter(end_dt__isnull=True).order_by('-start_dt').first()

    if current_temp <= 25:
        # => Température normale => on ferme l'incident s'il y en a un
        if open_incident:
            open_incident.end_dt = timezone.now()
            open_incident.save()
            print("[INFO] Incident fermé (température redevenue normale).")
        else:
            print("[INFO] Aucun incident en cours, température normale.")
    else:
        # => Température élevée
        if not open_incident:
            # 1. Créer un nouvel incident
            new_incident = Incident.objects.create(
                start_dt=timezone.now(),
                iteration=1
            )
            print(f"[INFO] Nouvel incident créé (ID={new_incident.id}). Itération=1")
            users_to_alert = get_users_to_alert(new_incident)
            send_custom_alerts(new_incident, users_to_alert)
        else:
            # Il y a déjà un incident en cours
            # Vérifier s'il y a encore des utilisateurs non acquittés
            users_to_alert = get_users_to_alert(open_incident)
            if users_to_alert:
                # Incrémenter l'itération
                open_incident.iteration += 1
                open_incident.save()
                print(f"[INFO] Incident en cours (ID={open_incident.id}) -> Itération={open_incident.iteration}")
                send_custom_alerts(open_incident, users_to_alert)
            else:
                # Tous les utilisateurs ont acquitté
                print("[INFO] Tous les utilisateurs ont acquitté l'incident. Pas d'escalade.")
                # Optionnel : Fermer l'incident si vous le souhaitez
                # open_incident.end_dt = timezone.now()
                # open_incident.save()


def get_users_to_alert(incident):
    """
    Retourne la liste des utilisateurs à alerter selon l'itération et les acquittements.
    """
    iteration = incident.iteration
    message = f"Alerte: température élevée (Incident #{incident.id}, itération {iteration})."

    # Récupérer les utilisateurs dans l'ordre d'escalade
    escalation_order = ['user1', 'user2', 'user3', 'admin']  # À adapter selon vos besoins
    users_to_alert = []

    for i in range(iteration):
        if i < len(escalation_order):
            username = escalation_order[i]
            user = get_user_by_username(username)
            if user and not Acknowledgment.objects.filter(incident=incident, user=user).exists():
                users_to_alert.append(user)

    return users_to_alert


def send_custom_alerts(incident, users):
    """
    Envoie des alertes personnalisées aux utilisateurs spécifiés.

    Args:
        incident (Incident): L'incident en cours.
        users (list of User): Les utilisateurs à alerter.
    """
    message = f"Alerte: température élevée (Incident #{incident.id}, itération {incident.iteration})."
    for user in users:
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

    # Ex. Telegram
    telegram_bot_token = "7859262503:AAGScp5W3u876LlZk1kcA7_S-dK1bmcuMVw"  # Remplacez par votre token
    if profile.telegram_id:
        send_telegram_alert(telegram_bot_token, profile.telegram_id, message)

    # Ex. WhatsApp
    if profile.twilio_account_sid and profile.twilio_auth_token and profile.whatsapp_number:
        send_whatsapp_alert(
            account_sid=profile.twilio_account_sid,
            auth_token=profile.twilio_auth_token,
            from_whatsapp='whatsapp:+14155238886',
            to_whatsapp=f'whatsapp:{profile.whatsapp_number}',
            message=message
        )

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
